# veritas_app/services/verification.py
import json
import logging
import httpx
from openai import AsyncOpenAI

from app.core.config import settings
from app.storage import db
from app.models.schemas import VerificationReport

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOOGLE_SEARCH_API_URL = "https://www.googleapis.com/customsearch/v1"


async def google_search(client: httpx.AsyncClient, query: str, num: int = 15) -> list[dict]:
    """Uses a shared httpx.AsyncClient to call the Google Search API."""
    if settings.GOOGLE_API_KEY == "not_set" or settings.GOOGLE_CX == "not_set":
        logger.warning("GOOGLE_API_KEY or GOOGLE_CX is not set. Returning mock search results.")
        return [{"title": "Mock Search Result", "link": "https://example.com", "snippet": "Google API keys are missing."}]

    params = {"key": settings.GOOGLE_API_KEY, "cx": settings.GOOGLE_CX, "q": query, "num": num}
    try:
        response = await client.get(GOOGLE_SEARCH_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return [{"title": i.get("title"), "link": i.get("link"), "snippet": i.get("snippet")} for i in data.get('items', [])]
    except httpx.HTTPStatusError as e:
        logger.error(f"Google Search HTTP error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during Google Search: {e}")
    return []


async def get_llm_report(client: AsyncOpenAI, place_data: dict, context: list) -> VerificationReport | None:
    """Uses a shared AsyncOpenAI client to generate a verification report."""
    if settings.OPENAI_API_KEY == "not_set":
        logger.warning("OPENAI_API_KEY is not set. Returning mock report.")
        mock_report_data = {
            "decision_suggestion": "review",
            "scores": {"source_trust": 0.5, "freshness": 0.5, "consistency": 0.5, "impact": 0.5, "total": 0.5},
            "differences": [{
                "field": "contact_phone", "old_value": place_data.get("contact_phone"),
                "new_value": "0987-654321 (simulated)", "evidence_url": "https://example.com",
                "evidence_quote": "This is a mock quote because the OpenAI API key is missing."
            }]
        }
        return VerificationReport.model_validate(mock_report_data)

    system_prompt = """
    你是一位嚴謹的資料核實專家。你的任務是基於「現有資料」和「網路檢索上下文」，找出資料的潛在變動，並以嚴格的 JSON 格式輸出。
    規則：
    1.  **僅使用提供的上下文**：絕不臆測或使用外部知識。
    2.  **必須提供引用**：每一項差異都必須包含 `evidence_url` 和 `evidence_quote`。若無確切證據，則不產生該項差異。
    3.  **格式嚴格**：`status` 欄位值僅限 "開放"、"暫停"、"關閉" 三者之一。
    4.  **僅輸出 JSON**：你的回應必須是單一且結構完整的 JSON 物件，符合指定的 Pydantic 模型，不含任何額外文字或解釋。
    5.  **分數邏輯**：`source_trust` (官方/新聞來源高)、`freshness` (近期內容高)、`consistency` (多來源一致性高)、`impact` (重要欄位變更高)、`total` (綜合評估)。
    6.  **決策建議**：若證據明確、來源可信、分數高 (如 >0.9)，建議 `approve`；若證據矛盾、來源薄弱或分數低，建議 `review`。
    """
    user_prompt = f"""
    [現有資料]
    {json.dumps(place_data, ensure_ascii=False, indent=2)}

    [網路檢索上下文]
    {json.dumps(context, ensure_ascii=False, indent=2)}
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        )
        report_json = json.loads(response.choices[0].message.content)
        return VerificationReport.model_validate(report_json)
    except Exception as e:
        logger.error(f"Error calling OpenAI API or validating its response: {e}")
        return None


async def run_global_verification_task(http_client: httpx.AsyncClient, openai_client: AsyncOpenAI):
    """The async background task for global verification."""
    try:
        logger.info("--- [Auto Task] Starting global verification ---")
        all_place_ids = list(db.mock_db["places"].keys())
        for place_id in all_place_ids:
            if not db.acquire_lock(place_id):
                logger.warning(f"[Auto Task] Skipping locked place: {place_id}")
                continue

            logger.info(f"[Auto Task] Processing place: {place_id}")
            try:
                place_data = db.get_place_by_id(place_id)
                if not place_data: continue
                query = f"{place_data.get('name', '')} {place_data.get('address', '')}"
                search_results = await google_search(http_client, query)
                if not search_results: continue
                report = await get_llm_report(openai_client, place_data, search_results)
                if not report: continue

                logger.info(f"[Auto Task] Report score for {place_id}: {report.scores.total}")
                if report.decision_suggestion == 'approve' and report.scores.total >= settings.AUTO_APPROVE_THRESHOLD:
                    updates = {diff.field: diff.new_value for diff in report.differences}
                    if updates:
                        db.update_place(place_id, updates)
                        logger.info(f"[Auto Task] Auto-approved and updated place: {place_id}")
            finally:
                db.release_lock(place_id)
        logger.info("--- [Auto Task] Global verification finished ---")
    finally:
        db.release_lock("global")
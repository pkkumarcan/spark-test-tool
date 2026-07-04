import os
import logging
import httpx
import yfinance as yf
from fastapi import Request, HTTPException

logger = logging.getLogger("spark.backend.financial_analyst")

async def conduct_financial_analysis(request: Request, ollama_url: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    ticker = body.get("ticker", "").strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol is required")

    logger.info(f"Financial Analyst Agent starting analysis for {ticker}")

    # Step 1: Fetch financial data via yfinance
    company_name = ticker
    info = {}
    try:
        t = yf.Ticker(ticker)
        # Fetch key metrics
        info = t.info
        history = t.history(period="1mo")
        
        # Summarize numerical data
        company_name = info.get("longName", ticker)
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")
        market_cap = info.get("marketCap", "N/A")
        forward_pe = info.get("forwardPE", "N/A")
        dividend_yield = info.get("dividendYield", "N/A")
        fifty_two_week_high = info.get("fiftyTwoWeekHigh", "N/A")
        fifty_two_week_low = info.get("fiftyTwoWeekLow", "N/A")
        summary = info.get("longBusinessSummary", "No summary available.")

        # Get historical prices (first/last/high/low in past month)
        price_data = []
        if not history.empty:
            for date, row in history.iterrows():
                price_data.append(f"{date.strftime('%Y-%m-%d')}: Close={row['Close']:.2f}, Volume={int(row['Volume'])}")
        price_history_summary = "\n".join(price_data[-10:]) # show last 10 trading days

        financial_context = (
            f"Company: {company_name} ({ticker})\n"
            f"Sector: {sector} | Industry: {industry}\n"
            f"Market Cap: {market_cap}\n"
            f"Forward P/E: {forward_pe} | Dividend Yield: {dividend_yield}\n"
            f"52-Week Range: {fifty_two_week_low} - {fifty_two_week_high}\n\n"
            f"Business Summary:\n{summary}\n\n"
            f"Recent Stock Price History (Last 10 Days):\n{price_history_summary}\n"
        )
    except Exception as e:
        logger.error(f"Failed to fetch yfinance data for {ticker}: {e}")
        financial_context = f"Company Ticker: {ticker}\nError: Could not retrieve yfinance metadata: {e}"

    # Step 2: Formulate analysis prompt
    analyst_prompt = (
        "You are an expert Wall Street financial analyst agent. Analyze the following financial metrics "
        "and stock price history. Write a comprehensive, professional investment analysis report. "
        "Structure your report with the following sections:\n"
        "1. Executive Summary\n"
        "2. Business Model & Market Position\n"
        "3. Financial Metrics Analysis\n"
        "4. Price Trend & Volatility Analysis\n"
        "5. Investment Thesis & Recommendation (Buy/Hold/Sell) with clear rationale\n\n"
        "Format the output beautifully in Markdown, including clear section headings, bullet points, and data tables where helpful.\n\n"
        f"Financial Context Data:\n{financial_context}"
    )

    ollama_payload = {
        "model": "qwen3:8b", # default
        "messages": [
            {"role": "system", "content": "You are a professional financial analyst AI agent."},
            {"role": "user", "content": analyst_prompt}
        ],
        "stream": False
    }

    # Model resolution
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{ollama_url}/api/tags")
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                if "qwen3:14b" in models:
                    ollama_payload["model"] = "qwen3:14b"
                elif "qwen3:8b" in models:
                    ollama_payload["model"] = "qwen3:8b"
                elif models:
                    ollama_payload["model"] = models[0]
    except Exception:
        pass

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=ollama_payload)
            if r.status_code == 200:
                report = r.json().get("message", {}).get("content", "").strip()
                return {
                    "status": "completed",
                    "ticker": ticker,
                    "company_name": company_name,
                    "report": report
                }
            else:
                raise HTTPException(status_code=502, detail=f"Ollama returned {r.status_code}: {r.text}")
    except Exception as e:
        logger.error(f"Financial analyst LLM query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

"""
Indicator Deep-Dive Content — BTCpulse
==========================================
Provides detailed explanations, context, and accumulation-focused summaries
for all indicators used in the dashboard.
"""

DEEPDIVES = {
    # --------------------------------------------------------------------------
    # Sentiment
    # --------------------------------------------------------------------------
    "Fear & Greed Index": {
        "what": "A composite sentiment score (0–100) derived from market volatility, momentum, social media trends, surveys, and BTC dominance. It aims to quantify the prevailing emotional state of the market.",
        "why_matters": "Serves as a powerful contrarian signal. Extreme fear often coincides with market bottoms, presenting prime buying opportunities, while extreme greed signals market tops and heightened risk.",
        "historical_context": "Historically, scores below 20 (Extreme Fear) have preceded significant price rallies. For example, the index hit a low of 5 in March 2020 before a massive bull run. Conversely, scores above 80 have often marked local or cycle tops.",
        "interpretation": "Low scores suggest widespread pessimism and potential undervaluation. High scores indicate euphoria and potential overvaluation. It is a measure of emotion, which can persist, so it is best used in conjunction with fundamental on-chain metrics.",
        "accumulation_summary": "When this metric is in the Extreme Fear range (<25), it historically aligns with stronger accumulation conditions and may indicate an improved risk-reward for buying Bitcoin."
    },
    "Altcoin Season Index": {
        "what": "A score (0-100) that measures whether capital is flowing into Bitcoin or altcoins. A score of 75 or higher suggests an \'Altcoin Season\', while a score of 25 or lower suggests a \'Bitcoin Season\'.",
        "why_matters": "Indicates market risk appetite. A Bitcoin Season suggests investors are risk-off, preferring the relative safety of BTC. An Altcoin Season suggests high risk appetite, which often occurs in the later, more speculative stages of a bull market.",
        "historical_context": "Major altcoin seasons, like the one in early 2021, coincided with massive rallies in smaller tokens but also marked a period of froth and local tops for Bitcoin before a correction.",
        "interpretation": "Low scores are generally healthier for a sustainable Bitcoin uptrend, as it shows capital is consolidating into the primary asset. High scores can be a warning sign of excessive speculation.",
        "accumulation_summary": "A low Altcoin Season Index (<25) is generally more favorable for Bitcoin accumulation, as it signals a flight to quality and a stronger, more focused market uptrend."
    },

    # --------------------------------------------------------------------------
    # On-Chain
    # --------------------------------------------------------------------------
    "MVRV Z-Score": {
        "what": "Measures the ratio between Bitcoin\'s Market Value (total market cap) and its Realised Value (the value of all coins at the price they were last moved on-chain). The Z-score normalizes this ratio.",
        "why_matters": "It identifies periods where Bitcoin is trading significantly above or below its \'fair value\' or cost basis. It is one of the most reliable on-chain indicators for identifying cycle tops and bottoms.",
        "historical_context": "The Z-score entering the red zone (>7) has accurately marked every major cycle top. Entering the green zone (<0) has signaled every major market bottom, representing periods of maximum opportunity.",
        "interpretation": "A Z-score below 0 suggests the market is trading below the aggregate cost basis of all holders, indicating deep undervaluation and capitulation. A score above 7 suggests extreme euphoria and overvaluation.",
        "accumulation_summary": "When the MVRV Z-Score is in the green zone (<0), it historically aligns with the strongest accumulation conditions, indicating the market is deeply undervalued relative to its on-chain cost basis."
    },
    "NUPL (Net Unrealized P&L)": {
        "what": "Represents the net unrealized profit or loss of all coins in the network as a percentage of the market cap. It is the difference between unrealized profits and unrealized losses.",
        "why_matters": "Directly measures holder profitability and sentiment. It provides a clear visualization of the market\'s psychological state, from capitulation to euphoria.",
        "historical_context": "The NUPL chart is color-coded by psychological state. Blue (Euphoria, >75%) has marked cycle tops, while Red (Capitulation, <0%) has marked cycle bottoms. The transition from Green (Optimism) to Blue is a key warning sign.",
        "interpretation": "A negative NUPL means the network as a whole is holding an unrealized loss, a sign of capitulation. A NUPL above 0.5 (50%) indicates significant unrealized profits and growing euphoria.",
        "accumulation_summary": "When NUPL is in the red (Capitulation) or orange (Hope) zones, it historically aligns with strong accumulation conditions, as it signals holder pain and the exhaustion of selling pressure."
    },
    "Puell Multiple": {
        "what": "The ratio of the daily issuance value of bitcoins (in USD) to the 365-day moving average of this value. It compares the current daily revenue of miners to its yearly average.",
        "why_matters": "Provides insight into miner profitability and stress. When the multiple is low, miners are earning less than their yearly average, which can lead to miner capitulation—a classic bottom signal. When high, miners are highly profitable, which often coincides with market tops.",
        "historical_context": "The Puell Multiple dropping into the green zone (<0.5) has marked major market bottoms in 2015, 2018, and 2020. Spiking into the red zone (>4.0) has coincided with major bull market peaks.",
        "interpretation": "A low value suggests miner revenue is under stress, potentially forcing less efficient miners to sell their BTC, exhausting selling pressure. A high value suggests miners are realizing significant profits and may soon begin selling, adding supply to the market.",
        "accumulation_summary": "When the Puell Multiple is in the green zone (<0.5), it historically aligns with strong accumulation conditions, as it signals miner capitulation and the potential end of a bear market."
    },
    "RHODL Ratio": {
        "what": "The ratio of the 1-week Realised Value HODL band to the 1-2 year Realised Value HODL band. It compares the value held by new buyers to that held by longer-term holders.",
        "why_matters": "Identifies cycle tops by showing when the market is overheated with new, speculative money relative to the smart money (long-term holders).",
        "historical_context": "The RHODL Ratio spiking into the red zone has been an exceptionally accurate predictor of major cycle tops. When new buyers dominate the network value, it signals euphoria and an impending correction.",
        "interpretation": "A high ratio indicates a large amount of value is held in recently moved coins, typical of bull market peaks. A low ratio indicates value is concentrated in the hands of long-term holders, typical of bear market bottoms and early bull markets.",
        "accumulation_summary": "A low RHODL Ratio historically aligns with favorable accumulation conditions, as it indicates that the market is dominated by long-term holders and speculative froth is low."
    },
    "Reserve Risk": {
        "what": "Measures the confidence of long-term holders relative to the current price. It is defined as Price / HODL Bank. A low Reserve Risk suggests high confidence and attractive risk/reward.",
        "why_matters": "When confidence is high and price is low (low Reserve Risk), it signals a strong buying opportunity. When confidence is low and price is high (high Reserve Risk), it signals an unattractive risk/reward.",
        "historical_context": "Reserve Risk entering the green zone has consistently marked periods of maximum accumulation opportunity. Entering the red zone has marked cycle tops where risk is highest.",
        "interpretation": "Low values indicate that long-term holders are confident and not selling, despite a low price. High values indicate that long-term holders are taking profits as the price is high, signaling an overheated market.",
        "accumulation_summary": "When Reserve Risk is in the green zone, it historically aligns with the strongest accumulation conditions, signaling high long-term holder confidence at a relatively low price."
    },

    # --------------------------------------------------------------------------
    # Price Model
    # --------------------------------------------------------------------------
    "Mayer Multiple": {
        "what": "The ratio of Bitcoin\'s current price to its 200-day moving average (200DMA). It measures how far the price has deviated from its long-term trend.",
        "why_matters": "Provides a simple and effective way to identify periods of potential over-extension or undervaluation relative to the long-term trend.",
        "historical_context": "Historically, a Mayer Multiple below 1.0 suggests the price is below its long-term trend and potentially undervalued. A multiple above 2.4 has historically signaled the start of speculative bubbles.",
        "interpretation": "A low multiple indicates the price is trading at a discount to its 200-day average, often a good time to buy. A high multiple indicates the price is trading at a premium, suggesting caution.",
        "accumulation_summary": "When the Mayer Multiple is below 1.0, it historically aligns with favorable accumulation conditions, as it suggests the price is trading at or below its long-term historical trend."
    },
    "200-Week MA Heatmap": {
        "what": "Visualizes the percentage increase or decrease of the Bitcoin price above or below its 200-week moving average. The color changes from blue (cold) to red (hot) as the price deviates further from the MA.",
        "why_matters": "The 200-week MA has historically served as a key long-term support level for Bitcoin. This indicator shows how \'overheated\' or \'oversold\' the price is relative to this ultimate floor.",
        "historical_context": "The price touching the 200-week MA (blue/purple colors) has consistently marked generational buying opportunities. Red/orange colors have signaled market tops.",
        "interpretation": "Blue colors indicate the price is near its long-term support, suggesting a low-risk entry point. Red colors indicate the price is far above its long-term support, suggesting high risk.",
        "accumulation_summary": "When the 200-Week MA Heatmap is in the blue or purple zones, it historically aligns with the strongest accumulation conditions, as the price is at or near its ultimate long-term support level."
    },
    "2-Year MA Multiplier": {
        "what": "Uses a 2-year moving average (730DMA) and a 5x multiple of that MA to identify potential cycle tops and bottoms.",
        "why_matters": "Provides a simple framework for long-term value. The 2-year MA has acted as a reliable long-term support, while the 5x multiple has marked major bull market peaks.",
        "historical_context": "When the price drops below the 2-year MA, it has signaled a generational buying opportunity. When the price exceeds the 5x multiple of the 2-year MA, it has signaled a major cycle top.",
        "interpretation": "Buying below the 2-year MA and selling above the 5x multiple has been a historically profitable, albeit simple, strategy.",
        "accumulation_summary": "When the price is below the 2-year moving average, it historically aligns with strong accumulation conditions, suggesting the market is in a deep value zone."
    },
    "Ahr999 Index": {
        "what": "A composite indicator that combines the Mayer Multiple and the price\'s deviation from its 200-day power-law regression model. It is designed to identify low-risk entry points for long-term investment.",
        "why_matters": "It smooths out short-term volatility and provides a clear signal for when to buy (index < 0.45) and when to consider taking profits (index > 1.2).",
        "historical_context": "The index dropping below 0.45 has consistently marked periods of low-risk accumulation. The index rising above 1.2 has signaled periods of increasing risk.",
        "interpretation": "A low index value suggests that both the price relative to its 200DMA and its long-term regression trend are low, indicating a strong buy signal. A high value suggests the opposite.",
        "accumulation_summary": "When the Ahr999 Index is below 0.45, it is explicitly signaling a strong accumulation opportunity based on its model, suggesting a favorable risk-reward for buying Bitcoin."
    },

    # --------------------------------------------------------------------------
    # Technical
    # --------------------------------------------------------------------------
    "Pi Cycle Top": {
        "what": "An indicator that has historically predicted cycle tops. It uses the 111-day moving average (111DMA) and a 2x multiple of the 350-day moving average (350DMA). A top is signaled when the 111DMA crosses above the 2x350DMA.",
        "why_matters": "Has been remarkably accurate in calling the exact day of the cycle peak in 2013, 2017, and 2021.",
        "historical_context": "The crossover event is a rare occurrence and should be treated as a major warning sign of an impending market top.",
        "interpretation": "The indicator is binary: either the lines have crossed (SELL) or they have not (HOLD/BUY). It is not useful for identifying bottoms, only tops.",
        "accumulation_summary": "This indicator is not used for accumulation signals. Its sole purpose is to signal a potential cycle top, which is a signal to reduce exposure, not add to it."
    },
    "RSI (14-Day)": {
        "what": "The Relative Strength Index is a momentum oscillator that measures the speed and change of price movements. It oscillates between 0 and 100.",
        "why_matters": "Identifies overbought or oversold conditions in the short term. A reading above 70 is considered overbought, while a reading below 30 is considered oversold.",
        "historical_context": "Daily RSI dropping below 30 has often marked local bottoms and good short-term buying opportunities. RSI above 70 has signaled potential for a short-term price correction.",
        "interpretation": "It is a short-term momentum indicator. In a strong uptrend, RSI can remain overbought for extended periods, and vice versa in a downtrend. It is best used for identifying divergences and short-term entry/exit points.",
        "accumulation_summary": "A daily RSI below 30 can signal a favorable short-term entry point for accumulation, but it should be confirmed with longer-term indicators as it is a measure of short-term momentum."
    },
    "RSI Weekly": {
        "what": "The Relative Strength Index calculated on a weekly timeframe. This provides a longer-term view of market momentum compared to the daily RSI.",
        "why_matters": "Identifies major overbought or oversold conditions on a macro scale. A weekly RSI above 90 is a strong warning of a cycle top, while below 45 has historically been a strong buy zone.",
        "historical_context": "Weekly RSI dropping below 45 has marked the bottom of every bear market. Weekly RSI rising above 90 has marked the peak of every bull market.",
        "interpretation": "It provides a much slower, more reliable signal than the daily RSI. It is excellent for identifying macro turning points in the market cycle.",
        "accumulation_summary": "When the weekly RSI is below 45, it historically aligns with the strongest accumulation conditions, signaling that the market is deeply oversold on a macro timeframe."
    },

    # --------------------------------------------------------------------------
    # Market Structure
    # --------------------------------------------------------------------------
    "BTC Dominance": {
        "what": "Measures Bitcoin\'s market capitalization as a percentage of the total cryptocurrency market cap. It shows how much of the market\'s value is concentrated in Bitcoin.",
        "why_matters": "Indicates the flow of capital between Bitcoin and altcoins. Rising dominance suggests a flight to safety or the start of a new bull market led by Bitcoin. Falling dominance suggests high risk appetite and an altcoin season.",
        "historical_context": "Historically, bull markets begin with rising BTC dominance as new capital flows into Bitcoin first. As the bull market matures, capital rotates into altcoins, causing dominance to fall.",
        "interpretation": "A rising dominance trend is generally a healthy sign for the overall market, while a rapidly falling dominance can be a sign of excessive speculation.",
        "accumulation_summary": "A rising or high level of BTC Dominance is generally a more favorable environment for Bitcoin accumulation, as it signals that market focus and capital flows are directed towards Bitcoin."
    },
    "CBBI (Bull Run Index)": {
        "what": "The Crypto Bitcoin Bull Run Index is a composite index of 8 different indicators to provide a single score for where we are in the bull run cycle.",
        "why_matters": "It attempts to simplify complex market dynamics into a single, easy-to-understand score, providing a \'you are here\' map for the market cycle.",
        "historical_context": "The index has been back-tested to show its effectiveness in identifying the different stages of past bull and bear markets.",
        "interpretation": "The index provides a score and a corresponding label (e.g., \'Bull Run in Full Swing\', \'Bear Market Bottom\'). It is a high-level summary of many other indicators.",
        "accumulation_summary": "When the CBBI indicates a \'Bear Market Bottom\' or \'Accumulation Phase\', it aligns with favorable conditions for buying Bitcoin, as it is a composite signal from multiple underlying metrics."
    },
    "BTC vs S&P 500": {
        "what": "Measures the relative performance of Bitcoin against the S&P 500 index. It shows whether Bitcoin is outperforming or underperforming traditional equities.",
        "why_matters": "Indicates Bitcoin\'s strength as an independent asset. When Bitcoin is outperforming the S&P 500, it demonstrates its value as a high-growth, risk-on asset. When it underperforms, it may be more correlated with macro trends.",
        "historical_context": "During major bull runs, Bitcoin has massively outperformed the S&P 500. During bear markets, it has often underperformed.",
        "interpretation": "A rising trend shows Bitcoin\'s strength. A falling trend shows relative weakness. It is useful for understanding Bitcoin\'s place in the broader financial landscape.",
        "accumulation_summary": "Periods where Bitcoin is showing sustained outperformance against the S&P 500 can signal a strong, independent bull market, which is a favorable condition for continued accumulation."
    },

    # --------------------------------------------------------------------------
    # Macro
    # --------------------------------------------------------------------------
    "Global Liquidity Index (GLI)": {
        "what": "A measure of the total amount of liquidity in the global financial system, primarily driven by the balance sheets of major central banks (e.g., the Fed, ECB, BoJ).",
        "why_matters": "Bitcoin, as a risk asset, is highly sensitive to changes in global liquidity. Expanding liquidity (money printing) is a major tailwind for Bitcoin. Contracting liquidity is a major headwind.",
        "historical_context": "The massive expansion of global liquidity in 2020-2021 directly fueled the last bull run. The contraction in 2022 was a primary driver of the bear market.",
        "interpretation": "A positive year-over-year growth in the GLI is bullish for Bitcoin. A negative growth rate is bearish. It is one of the most important macro drivers of the crypto market.",
        "accumulation_summary": "When the Global Liquidity Index is expanding, it provides a strong macro tailwind for Bitcoin, creating favorable conditions for accumulation as new money is flowing into the financial system."
    },
    "US Dollar Index (DXY)": {
        "what": "Measures the value of the United States dollar relative to a basket of foreign currencies. A rising DXY means the dollar is strengthening; a falling DXY means it is weakening.",
        "why_matters": "Bitcoin is priced in USD and has a strong inverse correlation to the DXY. A strong dollar (rising DXY) is typically bearish for Bitcoin, as it makes BTC more expensive in other currencies and signals a risk-off environment. A weak dollar (falling DXY) is bullish.",
        "historical_context": "The 2017 bull run coincided with a weak DXY. The 2022 bear market coincided with a very strong DXY.",
        "interpretation": "Look for a falling DXY as a confirmation of a risk-on environment that is favorable for Bitcoin. A rising DXY is a major warning sign.",
        "accumulation_summary": "A falling or weak US Dollar Index (DXY) historically aligns with favorable conditions for Bitcoin accumulation, as it signals a risk-on environment and makes Bitcoin cheaper for foreign investors."
    }
}

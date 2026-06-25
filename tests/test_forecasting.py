import unittest
import pandas as pd

from forecasting import prepare_daily_sentiment, forecast_sentiment


class TestForecastingSyntheticData(unittest.TestCase):
    def test_prepare_daily_sentiment_single_date_returns_synthetic_history(self):
        df = pd.DataFrame(
            {
                "date": ["2026-01-01"] * 5,
                "sentiment": [0.1, 0.2, -0.1, 0.05, 0.0],
            }
        )

        daily, synthetic_history = prepare_daily_sentiment(df)

        self.assertTrue(synthetic_history)
        self.assertEqual(len(daily), 30)
        self.assertEqual(daily["date"].nunique(), 30)
        self.assertTrue((daily["sentiment"] >= -1).all())
        self.assertTrue((daily["sentiment"] <= 1).all())

    def test_forecast_sentiment_single_date_returns_flag(self):
        df = pd.DataFrame(
            {
                "date": ["2026-01-01"] * 5,
                "sentiment": [0.1, 0.2, -0.1, 0.05, 0.0],
            }
        )

        forecast_df, synthetic_history = forecast_sentiment(df, forecast_days=7)

        self.assertTrue(synthetic_history)
        self.assertEqual(len(forecast_df), 7)
        self.assertIn("predicted_sentiment", forecast_df.columns)


if __name__ == "__main__":
    unittest.main()

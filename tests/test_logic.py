from unittest.mock import MagicMock, patch
from django.test import TestCase
from arbitrage_agent.core.logic import ask_agent
from langchain_core.messages import SystemMessage, HumanMessage

class AskAgentTest(TestCase):

    @patch('arbitrage_agent.core.logic.agent_app')
    def test_ask_agent(self, mock_agent_app):
        expected_response_text = "Analysis: Bitcoin shows a bullish trend."
        mock_response_message = MagicMock()
        mock_response_message.content = expected_response_text

        mock_agent_app.invoke.return_value = {
            "messages": [
                MagicMock(), # System Message
                MagicMock(), # Human Message
                mock_response_message # Final Agent Response
            ]
        }

        user_query = "Should I buy Bitcoin?"
        result = ask_agent(user_query)
        mock_agent_app.invoke.assert_called_once()

        args, _ = mock_agent_app.invoke.call_args
        input_payload = args[0]
        self.assertIn("messages", input_payload)
        messages = input_payload["messages"]
        self.assertEqual(len(messages), 2)

        # The first message should be the system instruction
        self.assertEqual(type(messages[0]), SystemMessage)

        # The second message should be the HumanMessage with the user's query
        self.assertEqual(type(messages[1]), HumanMessage)
        self.assertEqual(messages[1].content, user_query)

        # 4. Verify Result
        self.assertEqual(result, expected_response_text)

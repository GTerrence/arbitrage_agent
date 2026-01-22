from unittest.mock import MagicMock, patch
from django.test import TestCase
from arbitrage_agent.core.logic import ask_agent

class AskAgentTest(TestCase):

    @patch('arbitrage_agent.core.logic.create_agent')
    @patch('arbitrage_agent.core.logic.hub.pull')
    @patch('arbitrage_agent.core.logic.ChatGoogleGenerativeAI')
    def test_ask_agent_success(self, mock_chat_cls, mock_hub_pull, mock_create_agent):
        """
        Test that ask_agent initializes components correctly and returns the agent's output.
        """
        # 1. Setup Mocks
        # Mock the LLM instance
        mock_llm_instance = MagicMock()
        mock_chat_cls.return_value = mock_llm_instance

        # Mock the Prompt
        mock_prompt = MagicMock()
        mock_hub_pull.return_value = mock_prompt

        # Mock the AgentExecutor/Agent
        mock_agent_executor = MagicMock()
        mock_create_agent.return_value = mock_agent_executor

        # Define the expected output from the agent
        expected_response_text = "The price of Bitcoin is $50,000."
        mock_agent_executor.invoke.return_value = {"output": expected_response_text}

        # 2. Execute Function
        user_query = "What is the price of Bitcoin?"
        result = ask_agent(user_query)

        # 3. Verify Interactions

        # Check LLM initialization
        mock_chat_cls.assert_called_once_with(model="gemini-2.5-flash", temperature=0)

        # Check Hub Pull
        mock_hub_pull.assert_called_once_with("hwchase17/react")

        # Check Agent Creation
        # We can't easily check 'tools' unless we mock them in specific variables,
        # but we can verify it was called with the LLM and Prompt.
        args, _ = mock_create_agent.call_args
        self.assertEqual(args[0], mock_llm_instance) # 1st arg: llm
        # args[1] is tools (list)
        self.assertEqual(args[2], mock_prompt)       # 3rd arg: prompt

        # Check Execution
        mock_agent_executor.invoke.assert_called_once_with({"input": user_query})

        # 4. Verify Result
        self.assertEqual(result, expected_response_text)

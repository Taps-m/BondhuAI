import sys, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import bondhu_orchestrator as agent

class FollowupTests(unittest.TestCase):
    history=[{'role':'user','parts':[{'text':'Krishak Bandhu benefits?'}]}]
    def test_first_question_unchanged(self):
        with patch.object(agent.client.models,'generate_content') as call:
            self.assertEqual(agent.contextual_question('Hello'),'Hello')
            call.assert_not_called()
    def test_resolved_question_reaches_entire_rag_path(self):
        resolved='How many installments does Krishak Bandhu pay?'
        with patch.object(agent,'contextual_question',return_value=resolved), patch.object(agent,'route_question',return_value='RAG') as route, patch.object(agent,'answer_with_rag',return_value=(SimpleNamespace(text='Two installments.'),[])) as rag, patch.object(agent,'optimize_answer',return_value='Two installments.') as optimizer:
            result=agent.answer_question('How many installments?',self.history)
            route.assert_called_once_with(resolved)
            self.assertEqual(rag.call_args.args[0],resolved)
            optimizer.assert_called_once_with(resolved,'Two installments.')
            self.assertEqual(result['answer'],'Two installments.')
    def test_ambiguity_does_not_search(self):
        with patch.object(agent,'contextual_question',return_value=None), patch.object(agent,'route_question') as route:
            self.assertEqual(agent.answer_question('How much?',self.history)['route'],'CLARIFY')
            route.assert_not_called()
    def test_bad_resolver_response_fails_closed(self):
        for output in ('not json','{}','{"question":"", "needs_clarification":false}','{"question":"guess", "needs_clarification":true}'):
            with patch.object(agent.client.models,'generate_content',return_value=SimpleNamespace(text=output)):
                self.assertIsNone(agent.contextual_question('How much?',self.history))
    def test_resolver_failure_fails_closed(self):
        with patch.object(agent.client.models,'generate_content',side_effect=RuntimeError('offline')):
            self.assertIsNone(agent.contextual_question('How much?',self.history))

if __name__=='__main__': unittest.main()

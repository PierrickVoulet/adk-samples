import requests
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, TextPart, UnsupportedOperationError
from a2a.utils import new_agent_text_message
from a2a.utils.errors import ServerError
from google.adk import Runner
from google.adk.agents import SequentialAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.genai import types

class AgentExecutorWithRunner(AgentExecutor):
    """Executor that takes an SequentialAgent instance and initializes the ADK Runner internally."""

    def __init__(self, agent: SequentialAgent):
        self.agent = agent
        self.runner = None

    def _init_adk(self):
        if not self.runner:
            self.runner = Runner(
                app_name=self.agent.name,
                agent=self.agent,
                artifact_service=InMemoryArtifactService(),
                session_service=InMemorySessionService(),
                memory_service=InMemoryMemoryService(),
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise ServerError(error=UnsupportedOperationError())

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        self._init_adk() # Initialize on first execute call

        if not context.message:
            return

        user_id = context.message.metadata.get('user_id') if context.message and context.message.metadata else 'a2a_user'

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            await updater.submit()
        await updater.start_work()

        query = context.get_user_input()
        content = types.Content(role='user', parts=[types.Part(text=query)])

        try:
            session = await self.runner.session_service.get_session(
                app_name=self.runner.app_name,
                user_id=user_id,
                session_id=context.context_id,
            ) or await self.runner.session_service.create_session(
                app_name=self.runner.app_name,
                user_id=user_id,
                session_id=context.context_id,
            )

            final_event = None
            async for event in self.runner.run_async(
                session_id=session.id,
                user_id=user_id,
                new_message=content
            ):
                if event.is_final_response():
                    final_event = event

            if final_event and final_event.content and final_event.content.parts:
                response_text = "".join(
                    part.text for part in final_event.content.parts if hasattr(part, 'text') and part.text
                )
                if response_text:
                    await updater.add_artifact(
                        [TextPart(text=response_text)],
                        name='result',
                    )
                    await updater.complete()
                    return
            
            await updater.update_status(
                TaskState.failed,
                message=new_agent_text_message('Failed to generate a final response with text content.'),
                final=True
            )

        except Exception as e:
            await updater.update_status(
                TaskState.failed,
                message=new_agent_text_message(f"An error occurred: {str(e)}"),
                final=True,
            )
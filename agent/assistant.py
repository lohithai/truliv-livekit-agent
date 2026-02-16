import json

from livekit import agents, api, rtc
from livekit.agents import Agent, AgentSession, RunContext, function_tool, get_job_context

from config import HUMAN_TRANSFER_NUMBER
from prompts import TRULIV_SYSTEM_PROMPT
from tools import get_properties, get_room_availability, get_bed_availability, get_location


class TrulivAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=TRULIV_SYSTEM_PROMPT,
            tools=[
                get_properties,
                get_room_availability,
                get_bed_availability,
                get_location,
                self.transfer_to_human,
            ],
        )

    @function_tool()
    async def transfer_to_human(self, ctx: RunContext) -> str:
        """Transfer the call to a human support agent. Use this when the caller explicitly asks to speak to a person, or when you cannot resolve their issue."""
        await ctx.session.generate_reply(
            instructions="Tell the caller you're transferring them to a human agent and to please hold."
        )

        job_ctx = get_job_context()
        try:
            participants = job_ctx.room.remote_participants
            sip_participant = None
            for p in participants.values():
                if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                    sip_participant = p
                    break

            if sip_participant and HUMAN_TRANSFER_NUMBER:
                await job_ctx.api.sip.transfer_sip_participant(
                    api.TransferSIPParticipantRequest(
                        room_name=job_ctx.room.name,
                        participant_identity=sip_participant.identity,
                        transfer_to=f"tel:{HUMAN_TRANSFER_NUMBER}",
                    )
                )
                return "Call transferred successfully."
            else:
                return "I'm sorry, I couldn't transfer the call right now. Please call our support number directly."
        except Exception as e:
            print(f"Error transferring call: {e}")
            return "I'm sorry, I couldn't transfer the call right now. Please call our support number directly."

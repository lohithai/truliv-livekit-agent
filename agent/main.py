import json

from dotenv import load_dotenv

from livekit import agents, api, rtc
from livekit.agents import AgentServer, AgentSession, room_io
from livekit.plugins import cartesia, deepgram, google, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from assistant import TrulivAssistant
from config import AGENT_NAME, SIP_TRUNK_OUTBOUND_ID
from prompts import INBOUND_GREETING

load_dotenv(".env.local")

server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME)
async def truliv_agent(ctx: agents.JobContext):
    # Check if this is an outbound call by reading metadata
    phone_number = None
    if ctx.job.metadata:
        try:
            metadata = json.loads(ctx.job.metadata)
            phone_number = metadata.get("phone_number")
        except json.JSONDecodeError:
            pass

    # If outbound, place the SIP call
    if phone_number:
        sip_participant_identity = phone_number
        try:
            await ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=ctx.room.name,
                    sip_trunk_id=SIP_TRUNK_OUTBOUND_ID,
                    sip_call_to=phone_number,
                    participant_identity=sip_participant_identity,
                    wait_until_answered=True,
                )
            )
            print(f"Outbound call to {phone_number} answered successfully")
        except api.TwirpError as e:
            print(
                f"Error creating SIP participant: {e.message}, "
                f"SIP status: {e.metadata.get('sip_status_code')} "
                f"{e.metadata.get('sip_status')}"
            )
            ctx.shutdown()
            return

    # Create the agent session with STT-LLM-TTS pipeline
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="en"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=cartesia.TTS(model="sonic", language="en"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=TrulivAssistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # For inbound calls, greet the caller. For outbound, wait for the person to speak first.
    if phone_number is None:
        await session.generate_reply(instructions=INBOUND_GREETING)


if __name__ == "__main__":
    agents.cli.run_app(server)

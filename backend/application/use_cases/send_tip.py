from ...domain.ports.repository_ports import UserRepositoryPort, TipRepositoryPort, VideoRepositoryPort
from ...domain.entities.tip import Tip
from ..dtos.tip_dto import TipCreateDTO, TipResponseDTO

class SendTipUseCase:
    def __init__(self, user_repo: UserRepositoryPort, tip_repo: TipRepositoryPort, video_repo: VideoRepositoryPort):
        self._user_repo = user_repo
        self._tip_repo = tip_repo
        self._video_repo = video_repo

    def execute(self, dto: TipCreateDTO, sender_id: str) -> TipResponseDTO:
        sender = self._user_repo.get_by_id(sender_id)
        if not sender:
            raise ValueError(f"Sender with ID {sender_id} not found.")

        receiver = self._user_repo.get_by_id(dto.receiver_id)
        if not receiver:
            raise ValueError(f"Receiver with ID {dto.receiver_id} not found.")

        if dto.video_id:
            video = self._video_repo.get_by_id(dto.video_id)
            if not video:
                raise ValueError(f"Video with ID {dto.video_id} not found.")
            if video.creator_id != dto.receiver_id:
                raise ValueError(f"Receiver is not the creator of the video {dto.video_id}.")

        # In a real application, you would also handle:
        # 1. Deducting the amount from the sender's balance
        # 2. Adding the amount to the receiver's balance
        # 3. Handling payment gateway integration

        tip = Tip(
            sender_id=sender_id,
            receiver_id=dto.receiver_id,
            video_id=dto.video_id,
            amount=dto.amount,
            currency=dto.currency
        )
        saved_tip = self._tip_repo.save(tip)

        return TipResponseDTO(
            id=saved_tip.id,
            sender_id=saved_tip.sender_id,
            receiver_id=saved_tip.receiver_id,
            video_id=saved_tip.video_id,
            amount=saved_tip.amount,
            currency=saved_tip.currency,
            created_at=saved_tip.created_at
        )
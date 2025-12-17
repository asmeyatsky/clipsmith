import asyncio
from backend.infrastructure.repositories.database import create_db_and_tables
from backend.infrastructure.repositories.sqlite_video_repo import SQLiteVideoRepository
from backend.domain.entities.video import Video
import uuid

async def main():
    print("Creating tables...")
    create_db_and_tables()
    
    repo = SQLiteVideoRepository()
    
    print("Saving video...")
    video = Video(
        id=str(uuid.uuid4()),
        title="Test Video",
        description="Desc",
        creator_id="user1",
        url="http://test.com/vid.mp4",
        status="READY"
    )
    
    saved = await repo.save(video)
    print(f"Saved: {saved}")
    
    print("Finding all...")
    videos = await repo.find_all()
    print(f"Found {len(videos)} videos")
    for v in videos:
        print(f"- {v.title} ({v.id})")

if __name__ == "__main__":
    asyncio.run(main())

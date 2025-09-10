from workers.implementations import ExtractTextFromYtImpl
from workers.models import ExtractTextFromYtResponseModel
from youtube_transcript_api import YouTubeTranscriptApi

ytApi = YouTubeTranscriptApi()


class ExtractTextFromYt(ExtractTextFromYtImpl):
    def ExtractText(
        self, videoId: str, chunkSec: int = 30
    ) -> list[ExtractTextFromYtResponseModel]:
        ytApiData = ytApi.fetch(videoId, languages=["hi", "en"])
        chunkResponse: list[ExtractTextFromYtResponseModel] = []
        currentChunkText = []
        currentChunkStart = None

        for item in ytApiData.snippets:
            windowIndex = int(item.start) // chunkSec
            windowStart = windowIndex * chunkSec

            if currentChunkStart is None:
                currentChunkStart = windowStart

            if windowStart == currentChunkStart:
                currentChunkText.append(item.text)
            else:
                chunkResponse.append(
                    ExtractTextFromYtResponseModel(
                        videoId=videoId,
                        chunkText=" ".join(currentChunkText).strip(),
                        chunkUrl=f"https://www.youtube.com/watch?v={videoId}&t={int(currentChunkStart)}s",
                    )
                )
                currentChunkStart = windowStart
                currentChunkText = [item.text]

        if currentChunkText and currentChunkStart is not None:
            chunkResponse.append(
                ExtractTextFromYtResponseModel(
                    videoId=videoId,
                    chunkText=" ".join(currentChunkText).strip(),
                    chunkUrl=f"https://www.youtube.com/watch?v={videoId}&t={int(currentChunkStart)}s",
                )
            )

        return chunkResponse

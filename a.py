from youtube_transcript_api import YouTubeTranscriptApi

ytt_api = YouTubeTranscriptApi()
print(ytt_api.fetch("jVzZ5vJQuQ8",languages=['hi', 'en'])) 



# Inspiration
https://www.tiktok.com/@andreaspoly/video/7440981565246737710

For those of you that don't wish to navigate and wait for the video to load, a brother was fed up with his mom asking so many questions that he started making a power point for every movie. This hilarious yet relatable moment sparked our idea - what if we could create an AI companion that provides real-time context and answers questions during movie watching?

# What it does
CompOnion is like having that one friend who knows everything about movies sitting right next to you, except they never get annoyed when you ask "wait, who's that guy again?" for the fifth time. Multiple people can join virtual viewing sessions where our AI assistant explains plot points, identifies characters, and answers questions without you having to pause the movie. No more awkward silences or confused looks when something important happens!

# How we built it
We built CompOnion with a React frontend using Vite and a Flask backend with Flask-SocketIO for real-time WebSocket communication. The heart of the system runs on the multimodal Gemini API for AI analysis and a custom TMDB integration for movie metadata.

# Since we couldn't do real-time video analysis (even with a 4060 GPU), we built a preprocessing pipeline instead. Our VideoPreprocessor extracts key frames ahead of time, our YouTube integration handles video processing, and the ContextAgent works with our PromptConstructor to generate meaningful responses. SQLite handles session management and user data.

# Challenges we ran into
Our biggest reality check came when we realized we couldn't do true real-time video analysis - the processing demands were just too much. We had to pivot to preprocessing, figuring out how to extract meaningful frames without losing context. WebSocket synchronization between Flask and React was trickier than expected, especially for multi-user sessions. Getting our ContextAgent to construct prompts that give Gemini enough context for helpful responses took several iterations.

# Accomplishments that we're proud of
We pulled off a working AI video analysis system that actually understands movie content. The multi-user experience with synchronized sessions came together beautifully. Our preprocessing pipeline turned out to be a clever solution that works better than expected. The integration between React frontend, Flask backend, and real-time WebSockets is smooth and responsive, creating a system that enhances rather than interrupts the viewing experience.

# What we learned
Real-time video analysis is way more computationally expensive than we thought, and sometimes the best solution isn't the most obvious one. Working with multimodal AI taught us about prompt engineering and giving AI systems proper context. Building collaborative real-time applications with WebSockets revealed synchronization challenges we never considered. We learned that user experience design is critical when building entertainment companions - one wrong move and you're a distraction instead of a help.

# What's next for CompOnion
We want direct integration with streaming platforms and media players. Localized sessions where CompOnion automatically appears on your phone when you walk into a room with an active viewing session. Voice commands, smart TV integration, different AI personalities, and enhanced mobile support are all on the roadmap. We're also thinking about expanding beyond movies to TV shows and educational content, plus community features for shared viewing parties across distances.

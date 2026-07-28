## The Context
## The Idea

A few months ago, I came across the idea of an "LLM Wiki", explained in a 2026 [gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) by OpenAI co-founder and Anthropic pre-training specialist Dr. Andrej Karpathy, PhD. 

Karpathy explains that "\[m]ost people's experience with LLMs and documents looks like RAG: you upload a collection of files, the LLM retrieves relevant chunks at query time, and generates an answer". He suggests an alternative approach: having a language model build its own wiki, which it evolves over time. I thought this sounded like a pretty good idea. 

Now, I do want to point out some personal problems with the idea that "You never (or rarely) write the wiki yourself". I dislike this concept for a few reasons. 

Firstly, I prefer to have an understanding of what's being written. Anything worth taking notes on is either interesting or important, and I won't give up the joy of learning for a potential efficiency gain. 

Secondly, I enjoy the practice and creative control. I don't want to let my ability to write stagnate by farming it out to an LLM, and I find it morally dubious to allow one to generate text in this nature. 

Thirdly, I fear that an LLM would misunderstand, omit, or hallucinate important information, compromising the quality of my notes. If I write everything myself, I have only myself to blame if something is wrong, and I would rather have made an honest mistake than have been negligent in trusting an LLM to handle important information. 

And finally, I find that it would be a waste of tokens. This directly translates into a higher carbon footprint and other contamination of natural resources. Writing for myself is the more environmentally conscious option. 

So, I decided to adapt the idea into something that works for me: a personal wiki, plus an MCP server that allows a language model read-only access to what I've written, and gives it its own sub-section that can fully integrate with my own writing. 

## Prior Experiences

I used to be very into Notion. During high school, I kept literally everything in there. Every piece of homework, the notes for every class, everything down to what I had for lunch was written up in Notion and became part of a massive database. 

In school, this worked great. Class notes were searchable by subject, teacher, and textbook section. Homework could basically be forgotten about once submitted. School never really changed, so one database schema served me perfectly for years.

After leaving school, I grew apart from Notion. A fixed schema database didn't suit the workflow of my software job so well, since it's a lot more inconsistent. The problem I had with note-taking at this point was not at all writing, but retrieving. With no sensible organisational system, finding old information became near impossible. 

Beyond that, I had increasing concerns about privacy and data sovereignty, and now Notion has gone in on generative AI, too. 
## The Editor

Having discounted Notion as a possibility, I was in the market for a new editor. Something that could maintain rich connections between notes, but not too rigid. 

MediaWiki was immediately off the table. Self-hosting it would be way too much hassle, and it's optimised for reading rather than writing. 

I briefly experimented with VimWiki. I like that it's free and open source, plus it works with a tool that I'm already using, but I found it to be over-engineered for my use case. Vim motions work great for navigating code, but I found that they only get in my way during note taking, in which I write far more linearly and edit far less. 

From there, I jumped to VSCodium with plugins, but I found that to be too much as well. I didn't need autocomplete, git status, line count... eventually, I figured I just needed an editor that would let me write markdown and get out of the way. 

Eventually, I settled on Obsidian. It feels like the markdown just melts away as I write it, so I can focus completely on what I'm writing rather than fighting and getting distracted by the editor. Though it isn't open source, it has great data sovereignty, which works for me. I use the default theme, with no plugins. 

## The Wiki

On Tuesday 14th April, 2026, I started seriously note-taking again. Since then, I have written almost 16,000 words across 218 notes, with a total of 774 wiki-links. 

My notes include a daily log for every working day, and individual notes for people, companies, projects, places, and more. Many of these individual notes started out only as junctions to link work across different days, but evolved, e.g. to contain contact details for people, and release procedures for projects.   

After just 3 and a half months, my graph doesn't look anywhere near as cool as the ones people show on the internet. Perhaps that's due to the nature of how I use Obsidian, with less of a branching structure and more of a mesh due to daily notes. Or, maybe I just need to give it time to see the patterns emerge. 

## The Output

The real magic starts with the retrieval mechanism. I built a small app that accepts a question from the user, and uses an LLM to answer. 

At first, I experimented with a few different local LLMs, but I found their quality to be lacking. They were prone to hallucination, and had a tendency to talk in the first person when describing things I had done, which I found deeply unsettling. 

Ultimately, I decided to use GPT 5.4 over the OpenAI API, and have had none of those issues with it. I added $5.00 USD of credits to my OpenAI account, and in just over 100 days, I have used $3.93 USD - so at my current rate of usage, and not accounting for potential differences as my vault grows, the tool has a projected cost of $14.35 USD per annum. That's just 6% of the annual cost of ChatGPT plus. 

That wasn't very much use on its own, since the model alone was about as competent as early versions of ChatGPT, so I exposed some MCP tools. 

In the first iteration, I exposed equivalents of the following GNU coreutils: 

* `ls`, to list files in a directory 
* `cat`, to read the entire contents of a file 
* `grep`, to perform a regex search within a directory

Inspired by a project by a co-worker, I later added a semantic index lookup tool. Periodically (via a cron job), I run a program to generate embeddings for new and changed files. These "embeddings" can be thought of plotting thousands of different qualities of text on a many-dimensional graph, so that we can mathematically determine how similar two texts are in terms of content, sentiment, and more. I did this embedding using [BGE-M3](https://huggingface.co/BAAI/bge-m3) - I chose a local model because I didn't want to burn my OpenAI credit on embedding, and BGE-M3 specifically because of its support for multi-lingual scenarios (not all of my notes are in English). I then exposed an MCP tool to let the agent embed any text it wanted and surface a number of top matches. After convincing it to use this as its starting point via the system prompt, I noticed it make significantly fewer tool calls on average, since it helped surface relevant data more quickly. 

At one point, I also added a tool that acts like a limited version of `curl`. It can only make GET requests, and it respects robots.txt (acting with the User-Agent "ChatGPT-User"). I thought this might be useful for the agent to gain additional context about some niche concepts, but logs show it hasn't called this tool even once. 

Another failed experiment was allowing the LLM to integrate its own sub-section of the wiki. I gave it read-write access to a specific folder within the wiki, so that it could integrate with my own content via wiki-links, but even after giving it explicit instructions to use it, the LLM simply would not create anything beyond an activity log which it was explicitly instructed to keep. 
## The Results 

Overall I've found this greatly useful. I've been writing more than I have in years, and I've been able to find answers to questions in a few seconds, rather than digging around multiple sources for several minutes. 

I think it would be even better if I could add read access to services like Teams, Outlook, and Jira, but unfortunately I don't get permission to create API keys for those. 

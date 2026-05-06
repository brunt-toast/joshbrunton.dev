---
title: I automated by TBR list
date: 2026-05-06
tags: [Books, Programming]
---

This is going to get a little mathsy at times, but I've tried to write for a general, non-techy audience. If maths scares you, feel free to skip over it. 

## The Idea 

When you go to the library, books are usually organised by topic, and then by author's name. This is generally a great system: if you know exactly what you're looking for, you know exactly where to find it, and if you know vaguely which subject you want to read about, you know roughly where to look. 

But what if you want to introduce new parameters to your search? Perhaps you want books on a particular subject with a particular perspective or writing style. That's difficult to determine from a bookshelf, and even internet searches will have trouble with such queries. 

I thought to myself, what if we could organise books in by more than just two properties? Perhaps in addition to going along a shelf to browse by author, you could look up and down shelves to browse by, say, readers' ideal level of expertise? Add in some depth and browse forward and backwards to browse by the length of the book? I imagined an *n*-dimensional library, where readers could browse in all sorts of imaginary directions to find the perfect book. 

Then it occurred to me: We *can* organise things in more than just 2 dimensions, using the magic of computers and maths! If we dilute the essence of a book into some numerical representation of all its qualities, we can arrange them by all those qualities simultaneously and browse based on their distance from a known point! 

## Ethical Considerations

As with all software, there are some ethical considerations to be had. I'd say that the considerations here are particularly important, especially in this day and age. 

Generative "AI" is, of course, awful. In the software world it creates countless bugs and deletes production databases, and in the creative world, companies are using its soulless, stolen "art" to devalue the hard work of artists, jeopardise their income, and give ugly and meaningless slop to consumers. This project doesn't use any generative models. It uses a "text transformer", which have been used for searching and semantic analysis since long before the advent of ChatGPT. It is fundamentally incapable of generating any "new" text. This is not "AI" as it has come to be known by the general populaton; it is machine learning, a decades-old practice with many wonderful applications. All the input data I used comes from Project Gutenberg, a library of over 75,000 free ebooks with expired copyright or which are dedicated to the public domain. All the work here happened on my own hardware, meaning I never uploaded any content to a service which might use it to train their own large language models. In summary: nobody is losing out on any money or other material gain because of what I've done here. 

I'm also mindful of the dangers of staying in one's comfort zone, and how important it is to read about a wide variety of topics from a range of perspectives. If I just recommend a book that's almost exactly like what you just read, and then again, and again, you'll stay within a very small echo chamber. To mitigate this, I added an "adventure" value (more on that later) to introduce a bit of deviance from the exact most similar work to what you asked for. 

## Techy stuff

All the code I wrote for this is was in C#/.NET. I used the Xenova All MiniLM L6 V2 (an ONNX model released under Apache 2.0, which embeds text in 384 dimensions) on a computer with a 3.7GHz Intel W-1290P CPU. As previously mentioned, input data comes from Project Gutenberg. 

It's worth noting that I have a very rudimentary understanding of machine learning. I'm no mathematician, and I see ML as more of a tool that I can use than a topic I am interested in. Someone who is more experienced in the field would probably be able to make a much higher quality solution than I'm doing here. 

## Maths 1: Building The Library

This step isn't actually that mathematically challenging for us, since the machine learning library does a lot of the work for us. 

The first part of encoding a text is splitting it into chunks. Our machine learning model can't handle whole books at once, so we need to feed it a bit at a time. I used a very primitive chunking algorithm, just splitting the text into 1000-character pieces. 

Next, we need to translate our chunks into lists of "tokens", which the machine learning model can understand. For tech-savvy readers, I used a bert tokenizer. The model is limited less on text length and more on token count, and 1000 characters of text doesn't always split into the same number of tokens. For the best results, it's important to choose a chunk size that is sensible for your model's maximum token count, and make sure to chop off any above the limit after tokenizing. 

To fit with the constraints of the code, we also have to create token type IDs from sequences, and an attention mask. These aren't really relevant to our use case, they just tell the model what to pay attention to, and in our case, we want to pay attention to everything. 

Each of the things we've generated - the input IDs, token type IDs, and attention mask - are all simple lists. We have to transform them into "tensors", that is, a list of lists of lists (et cetera... up to n many lists), so the model can understand it. 

Next up is where the magic happens. By magic, I do mean Arther C. Clarke's "science we don't understand yet" - it's basically an opaque box, in that text goes in and numbers come out and nobody fully understands what happens in the middle. The list of numbers it spits out, representing the themes and styles of the text, are called the "embedding". These numbers aren't particularly meaningful on their own (there isn't, for example, a single number that represents a "comedy" score). They only have meaning relative to each other, in that two lists of similar numbers represent similar texts, and two lists of very different numbers represent very different texts. 

Since a single text is a list of multiple chunks, and we generate one list per chunk, a text is essentially a list of lists right now. We bring this down to a list of numbers manually (without help from the ML library) by taking the mean average of every chunk, and then normalising them (using euclidean normalisation) to make sure they still fit the constraints of what the numbers should be. 

With that, we have reduced a whole text to a sequence of numbers which indicate its themes and styles. Do this to the whole library and we can place every book in a precise location on a 384-dimensional grid (the number of dimensions varies per ML model). 

The speed at which this algorithm processes texts depends very highly on the length of the text and the model used. For most Project Gutenberg books, the model I used takes about 10 seconds, which works out to about 200 hours to embed the whole library on my computer. The work is very CPU-intensive, using about 50% of my available resources, but the RAM usage isn't too high, using about 700MiB on average (with a few texts loaded into memory at any given time). 

## Maths 2: Making A Recommendation 

To make a recommendation, we first need to build an embedding of what the user wants. There are two factors that we need to consider: mood and history. 

"Mood" is what the user wants or doesn't want. We represent this by embedding a list of desirable traits and a list of undesirable traits, and then turn these into a single embedding by literally doing the maths "positive traits + (-1 * negative traits). 

"History" is a lot more complicated. We need to consider what the user has read, how much they liked it, and introduce a recency bias to account for changing tastes over time. First, we'll need to adjust the weight of a book based on its review score. Going with a simple 5-star review system, where 3 is "neutral", we can multiply it based on that. We'll also add a recency bias by adding a "half-life" to every book, which would differ based on how quickly the user gets through books. This means that the influence of a book will be cut in half after a certain amount of time passes. If we multiply these weights together, we get a weight that is positive if the user liked the book, and more important if they read it more recently. We can then perform our mean average and euclidean normalisation to create a single representative embedding. 

We merge mood and history simply by once again taking the mean average and normalising it. This way, the user's mood is just as important as their history. 

Finally, we introduce something called "adventure" (because "adventurousness" is too difficult to spell). We don't actually need any machine learning for this one. We take a value from 0% to 100% and multiply that by the number of books the user hasn't read yet. Then, we sort all books by similarity to the desired embedding and recommend the book at that index - so if they choose 0% adventure, they'll get the 1st most similar book, and if they choose 100%, they'll get the last most similar book, i.e., the least similar.

Here's where it gets mathsy. This part is very skippable if you don't care about implementing something similar for yourself.

Our inputs are: 

* Adventure $a$, where $0 \le a \le 1$
* Ratings per book $r_i$ for book $i$, where $1 \le r_i \le 5$
* Time since read $t_i$ for book $i$
* Half-life $h$
* Positive mood $m_p$
* Negative mood $m_n$
* Total number of unread books $n$

We'll need standard algorithms defined as:

* Mean average: $\bar x = {{\Sigma^n_{i=1}x_i}\over{n}}$
* Euclidean normalisation: $\hat{x} = \frac{x}{\|x\|_2}$
* Embed: $v_i = \text{magic...}$

Now for our custom weight adjustment algorithm. To get the weight of a book $i$ that was read $t$ time ago and rated $r$ stars: 

$$
w_{r_i} = 
\begin{cases}
r_i - 3 & \text{if } r_i \lt 3
\\ 
r_i - 2 & \text{if } r \ge 3
\end{cases}
\\
w_{t_i} = 2^{t_i/ h}
\\
w_i = w_{r_i} \cdot w_{t_i}
$$

To apply this weight to each book and generate the average: 

$$
v_{books} = {{\Sigma_iw_i \cdot v_i}\over{\Sigma_i |w_i|}}
$$

To find the embedding for the mood: 

$$
v_{mood} = {v_{m_p} - v_{m_n}}
$$

Then we put those together and determine the embedding of the ideal book: 

$$
v_{final} = \hat{\bar{\hat{\bar{v_{mood}}} \cdot \hat{\bar{v_{books}}}}}
$$

We sort every text by their difference from $v_{final}$. We define the difference as the dot product (a common algorithm from linear algebra that measures the similarity of two lists of equal size): 

$$
a \cdot b = \Sigma^n_{i=1}a_ib_i
$$

Finally, within the list of books sorted by their difference from our idealised embedding, we pick the book at index $i$, defined based on our library size and adventure value:

$$
i = \lceil (a \cdot n) \rceil 
$$

Generating embeddings for our library takes ages, but getting recommendations takes about 3 seconds, be it on the scale of 10 texts or 10,000. Most of that time is spent actually embedding the query data, so the actual computation is incredibly fast. 

## So, does it work? 

Yep! 

I gave input data along the following lines: I've just read the US Declaration of Independence and rated it 5 stars. I want 5 recommendations that are direct, political, and historic; nothing modern, comedic, or fictional. I'm feeling 0% adventurous (and not that it matters for this case, but I have 12,000 books and a half-life of 30 days).

I got the following recommendations: 

* Inaugural Address of Franklin Delano Roosevelt
* Operation R.S.V.P.
* Address by Honorable Franklin K. Lane, Secretary of the Interior at Conference of Regional Chairmen of the Highways Transport Committee Council of National Defense
* Inaugural Presidential Address
* The Act of Incorporation and the By-Laws of the Massachusetts Homeopathic Medical Society

Exactly what I asked for! 

Then, I swapped it around. Rated the Declaration of Independence as 1 star, and flipped by desirable and undesirable traits. I got: 

* Greybeards at Play: Literature and Art for Old Gentlemen
* The Adventure of Two Dutch Dolls and a 'Golliwogg'
* The World Turned Upside Down
* Sonnets on Sundry Notes of Music
* Amusing Trial in which a Yankee Lawyer Renders a Just Verdict

I'd say that's pretty opposite to the Declaration of Independence in style, theme, and content. 

## Afterword 

Overall I think this has been a pretty cool project. 

There's definitely a lot of room to improve it still. Some of my ideas include: 

* Keeping track of users' book ratings 
* Improving quality by testing different models, tokenizers and chunk sizes 
* Adding a proper user interface (right now it's just a program that I edit and run)
* Working out if there's a good algorithm to choose half-life, rather than letting the user decide 

After working out some subtleties, I plan to load up my program with books I've already read and see if it gives me recommendations that I enjoy or are relevant to a specific query. 
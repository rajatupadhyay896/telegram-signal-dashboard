import snscrape.modules.twitter as sntwitter

query = "nifty OR banknifty"

tweets = []

for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
    if i > 50:
        break

    tweets.append(tweet.content)

# print results
for t in tweets:
    print(t)
    print("-" * 50)

# Creating a personalized movie score based on my historic rating patterns

## About the project
Before I watch a movie, I usually check out IMDB and Rotten Tomatoes. Since IMDB displays the Metascore too, this quick round of research gives me 4 different datapoints on how different audiences rated the movie. When these ratings are very different, it's hard to predict what my rating would be. So I scraped these ratings for the movies I rated on IMDB and fit two simplistic models.

## Data
I've been rating movies on IMDB for years. I exported this data (`ratings.csv`) and scraped Metacritic and Rotten Tomatoes for the films that I rated. Therefore the final dataset has a 'Your Rating' column along with four columns used as features in the models
-'IMDB rating'
-'Metascore'
-'Rotten Tomatoes Audience Score'
-'Rotten Tomatoes Critics Score'

## The models
The models are super simple on purpose, so that their conclusion could be applied even without a computer or calculator nearby. Therefore the two models are:

1. A linear regression on the four rating features rescaled to the 0-10 range. The resulting coefficients can therefore be used to quickly calculate a weighted average of the four ratings to predict my own rating of a movie.
2. A shallow and pruned down single decision tree to classify movies into a "Like" (higher than or equal to an own rating of 7) or "Dislike" category. 

## Conclusions

- The weights resulting from the linear regression for IMDB rating, Metascore, RT Critics score and RT Audience score respectively are 1.07, -0.11,  0.08 and -0.05. I found this surprising, I thought that my preference would align most with the RT Audience score. I suspect, that since I rate movies on IMDB, the IMDB score strongly biases my ratings. This way, the resulting weighted average from this model will pretty much be just the IMDB score, so the model probably won't change my life for the better. It's probably good to mention that a linear model that uses this little information was probably not going to change my life for the better anyways. 
- This is the resulting decision tree:
![My movie rating decision tree](https://github.com/MateVaradi/MyMovieRatings/blob/main/my_decision_tree.png)
The problem with this model is also apparent from the decision tree. The dataset is unbalanced, as I _like_ too many movies. For the record, this is not becuase I like every movie I watch, but becuse I pre-select and watch only movies that I think I would like (this may come as a huge surprise looking at this analysis). Apart from the unbalancedness, I think a model like this could be better able to capture an underlying pattern in my rating behavior, for example I will not necessarily enjoy an artistic, but boring movie that is highly rated by critics but not so much by a more general audience (although there is probably a critics-bias that results in me giving a decent score to an artistic film despite my unfavorable opinion of it). 




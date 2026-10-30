# exoplanet_triage
DOI 10.26133/NEA4

# Kepler Candidate Triage

Live app: https://exoplanettriage-ctpjuclsfzudjjf9wwcuvd.streamlit.app

## What this is

The Kepler space telescope found thousands of dips in starlight that might be planets. Each one is called a candidate. Many of them are not planets. Checking a candidate takes expensive telescope time and expert work, so a team can only check so many.

This project ranks unresolved candidates by how likely they are to be real planets, so a vetting team (the experts who check candidates) can look at the best ones first. The question is not "is this a planet?" but "which ones should we check first?"

Good here means two things:
- Precision at k (of the top k objects ranked, the share that are real planets) is high.
- The probabilities can be trusted. When the model says 90%, about 90% should be real planets. This is called calibration.

I do not use accuracy as the main number. A model that always says "not a planet" is already right about 64% of the time and finds nothing.

## Data

NASA Exoplanet Archive, Kepler Objects of Interest cumulative table. 9,564 rows. Downloaded on [add date from your file name].

- Confirmed planets: 2,748
- False positives (signals that look like planets but are not): 4,839
- Candidates (unresolved, no known answer): 1,977

I trained and tested only on the 7,587 resolved rows. At the end I used the model to rank the 1,977 candidates.

## Method

1. Leakage check. Leakage means the model can see the answer. I removed columns that are the vetting verdict or only exist after a decision, such as kepler_name, koi_score, koi_pdisposition, koi_comment and the four koi_fpflag columns. I used crosstabs (counts of each label for each value of a column) to check. For example, whenever koi_fpflag_co was 1, the object was always a false positive.
2. Features. 83 numeric columns: the shape of the dip, how strong the signal is, star properties, and the pixel checks (which test whether the dip comes from the target star or a neighbour). I removed IDs, links, empty columns, columns that never change, and the sky position.
3. Split by star. One star can have several objects, and they share star measurements. I kept each star's objects in the same set: 60% train, 20% validation, 20% test. The test set was used once, at the end.
4. Preprocessing for the linear model: fill gaps with the median, a signed log (a log that also works on zero and negative numbers), and scaling. All of it was learned from the training set only. XGBoost used the raw columns.
5. Models. Baselines first (random ranking, ranking by signal strength only), then logistic regression, then XGBoost. The final model is XGBoost with 300 trees, learning rate 0.05 and depth 3. I refit it on train plus validation before the test.
6. Uncertain columns. I tested 5 columns I was not sure about (koi_bin_oedp_sig, koi_count, koi_tce_plnt_num, ra, dec), one at a time. None helped clearly, so none were used. The text columns were not tested.

## Results

Validation, precision at 572 (572 is the number of real planets in validation):
- Random ranking: 0.348
- Signal strength only: 0.313
- Logistic regression: 0.939
- XGBoost: 0.958

Log loss (lower means better probabilities): logistic regression 0.131, XGBoost 0.092.

Test, final model (1,546 objects, 587 planets):
- Precision in the top 50: 1.0
- Precision in the top 100: 1.0
- Precision in the top 300: 0.997
- Precision in the top 587: 0.973
- Log loss: 0.073
- Accuracy: 0.979

Calibration, checked on validation:
- Scores above 0.9 (533 objects): 98.7% were real planets.
- Scores from 0.5 to 0.9 (37 objects): the model said 74% on average, but 57% were real. It is overconfident here, and this group is small.

Ranking the 1,977 candidates:
- 17% score above 0.9, 36% score between 0.1 and 0.9, 47% score below 0.1.
- On the test set it was 34% above 0.9 and 7% in the middle, so the model is much less sure about candidates.
- The rank agreement with the Kepler team's own koi_score is 0.417 (Spearman, from -1 to 1).

## Where it fails

Candidates are different from the objects I trained on. I tested this by training a model to tell resolved objects from candidates (adversarial validation). It got an AUC of 0.904 (0.5 means the groups look the same, 1.0 means they are completely different). The main difference is signal strength: the median signal-to-noise is 11.0 for candidates and 31.1 for resolved objects.

So the test results are probably too good for candidates. I cannot measure how much, because candidates have no answers.

I also read the 15 worst mistakes of each kind on the test set. This is a small sample, so it is a lead and not proof.
- False positives the model trusted often had comments about light from a nearby star or a copy of another signal, and they had a small pixel offset.
- Real planets the model rejected often had a large pixel offset. Many were also weak signals or had long periods.

My reading is that the model relies a lot on the pixel offset, and it fails when that measurement is unreliable.

## Limits

- Scores are a ranking guide, not confirmed odds. This project does not confirm any planet.
- Probabilities between 0.5 and 0.9 are overconfident.
- I used one split and one run, so small differences between models are noise.
- The pixel checks are part of the evidence the Kepler team used for its own verdicts, so the model partly learns their rules.
- Text columns were not tested.

## How to run

The app only needs the ranking file in app/.

    pip install -r requirements.txt
    streamlit run app/app.py

With Docker:

    docker build -t kepler-triage .
    docker run -p 8501:8501 kepler-triage

Then open http://localhost:8501.

requirements.txt is for the app only. The notebook also needs scikit-learn, xgboost, scipy and joblib.

To rebuild everything, download the data with this query and run the notebook data_retrieval.ipynb:

    https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+*+from+cumulative&format=csv

## Credit

Data: NASA Exoplanet Archive, Kepler Objects of Interest (cumulative table), DOI 10.26133/NEA4.

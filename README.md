# QCFlow: A Quantum Computations Tracking Platform

[![Apache 2 License](https://img.shields.io/badge/license-Apache%202-brightgreen.svg?style=for-the-badge&logo=apache)](https://github.com/mlflow/mlflow/blob/master/LICENSE.txt)

QCFlow is an open-source platform, repurposed from [MLFlow](https://github.com/mlflow) to assist quantum computing practitioners and teams in handling the challenges of quantum computing projects tracking. QCFlow focuses on the complete process of quantum computations, ensuring that each phase is manageable, traceable, and reproducible.

---

The core components of QCFlow are:

- [Experiment Tracking](link) 📝: A set of APIs to log jobs, quantum circuits, params, target devices, and results in QC experiments and compare them using an interactive UI.

- [Model Packaging](link) 📦: A standard format for packaging a model and its metadata, such as dependency versions, ensuring reliable deployment and strong reproducibility.

- [Model Registry](link) 💾: A centralized model store, set of APIs, and UI, to collaboratively manage 

- [Evaluation](link) 📊: A suite of automated model evaluation tools, seamlessly integrated with experiment tracking to record model performance and visually compare results across multiple models.

TR TODO: Insert dashboard image here. 

## Installation (REVISIT)

To install the QCFlow Python package, run the following command:

```
pip install qcflow
```
**The package, however, is not yet ready.**

## Documentation (REVISIT)

Official documentation for QCFlow can be found at [here](link). The coumentation, however, is not yet prepared.

## Usage (REVISIT)

### Experiment Tracking ([Doc](link))

The following examples trains a simple regression model with scikit-learn, while enabling MLflow's [autologging](https://mlflow.org/docs/latest/tracking/autolog.html) feature for experiment tracking.

TODO TR: Can I do something similar for `qiskit`?

```python
import mlflow

from sklearn.model_selection import train_test_split
from sklearn.datasets import load_diabetes
from sklearn.ensemble import RandomForestRegressor

# Enable MLflow's automatic experiment tracking for scikit-learn
mlflow.sklearn.autolog()

# Load the training dataset
db = load_diabetes()
X_train, X_test, y_train, y_test = train_test_split(db.data, db.target)

rf = RandomForestRegressor(n_estimators=100, max_depth=6, max_features=3)
# MLflow triggers logging automatically upon model fitting
rf.fit(X_train, y_train)
```

Once the above code finishes, run the following command in a separate terminal and access the MLflow UI via the printed URL. An MLflow **Run** should be automatically created, which tracks the training dataset, hyper parameters, performance metrics, the trained model, dependencies, and even more.

```
mlflow ui
```

### Evaluating Models ([Doc](...))

TR TODO: Can I automatically compare the results of two quantum circuits execution, (eg. with simulators)? 

TR TODO: Can I set automatic evaluations of some inequalities violations? 

The following example runs automatic evaluation for question-answering tasks with several built-in metrics.

```python
import mlflow
import pandas as pd

# Evaluation set contains (1) input question (2) model outputs (3) ground truth
df = pd.DataFrame(
    {
        "inputs": ["What is MLflow?", "What is Spark?"],
        "outputs": [
            "MLflow is an innovative fully self-driving airship powered by AI.",
            "Sparks is an American pop and rock duo formed in Los Angeles.",
        ],
        "ground_truth": [
            "MLflow is an open-source platform for managing the end-to-end machine learning (ML) "
            "lifecycle.",
            "Apache Spark is an open-source, distributed computing system designed for big data "
            "processing and analytics.",
        ],
    }
)
eval_dataset = mlflow.data.from_pandas(
    df, predictions="outputs", targets="ground_truth"
)

# Start an MLflow Run to record the evaluation results to
with mlflow.start_run(run_name="evaluate_qa"):
    # Run automatic evaluation with a set of built-in metrics for question-answering models
    results = mlflow.evaluate(
        data=eval_dataset,
        model_type="question-answering",
    )

print(results.tables["eval_results_table"])
```

## Community (REVISIT)

TBD

## Contributing

We happily welcome contributions to QCFlow! Please see our
[contribution guide](CONTRIBUTING.md) to learn more about contributing to MLflow.

## Core Members

QCFlow is currently maintained by [me](https://github.com/Tomev).

MLflow, the basis of QCFlow, is currently maintained by the following core members with significant contributions from hundreds of exceptionally talented community members.

- [Ben Wilson](https://github.com/BenWilson2)
- [Corey Zumar](https://github.com/dbczumar)
- [Daniel Lok](https://github.com/daniellok-db)
- [Gabriel Fu](https://github.com/gabrielfu)
- [Harutaka Kawamura](https://github.com/harupy)
- [Serena Ruan](https://github.com/serena-ruan)
- [Weichen Xu](https://github.com/WeichenXu123)
- [Yuki Watanabe](https://github.com/B-Step62)
- [Tomu Hirata](https://github.com/TomeHirata)

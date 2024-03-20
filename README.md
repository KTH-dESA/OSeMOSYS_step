# OSeMOSYS step

This repository contains a set of scripts to conduct model runs with limited
foresight with OSeMOSYS models.

# Directory Structure

Before the workflow has been run, the directory will look like what is shown below:

```bash
OSeMOSYS_STEP
├── data
│   ├── scenarios
│   │   ├── 1
│   │   │   ├── *.csv
│   │   │   ├── *.csv
│   │   │   └── ...
│   │   ├── 2
│   │   │   ├── *.csv
│   │   │   ├── *.csv
│   │   │   └── ...
│   │   └── 3
│   │       ├── *.csv
│   │       ├── *.csv
│   │       └── ...
│   └── data.txt
├── model
│   └── osemosys.txt
├── results
├── src
│   ├── *.py
│   ├── *.py
│   └── ...
└── steps
```

## `data`
The `data/` directory holds information on the reference model, and each
scenario you want to run. All scenario information must be nested under a
`scenarios/` subdirectory.

### `data/scenarios`
The `data/scenarios` subdirectory holds information on the options (or decisions)
that the model can make. Within this directory, numerically ordered subdirectories
are created to hold information on each step. For example, if there are 5 steps
in the model run, there will be 5 subdirectories, each labeled 0 through 4.

Within each `data/scenarios/#` subdirectory, CSV files hold information
on the options that can be made. Each CSV file must follow the formatting
shown below.

|             PARAMETER            | REGION | TECHNOLOGY | OPTION | YEAR | VALUE     |
|:--------------------------------:|:------:|------------|--------|:----:|-----------|
| TotalAnnualMaxCapacityInvestment | UTOPIA | COAL       | 0      | 2020 | 999999999 |
| TotalAnnualMaxCapacityInvestment | UTOPIA | COAL       | 0      | 2021 | 999999999 |
| ...                              | ...    | ...        | ...    | ...  | ...       |
| TotalAnnualMaxCapacityInvestment | UTOPIA | COAL       | 0      | 2049 | 999999999 |
| TotalAnnualMaxCapacityInvestment | UTOPIA | COAL       | 0      | 2050 | 999999999 |
| TotalAnnualMaxCapacityInvestment | UTOPIA | COAL       | 1      | 2020 | 0         |
| TotalAnnualMaxCapacityInvestment | UTOPIA | COAL       | 1      | 2021 | 0         |
| ...                              | ...    | ...        | ...    | ...  | ...       |
| TotalAnnualMaxCapacityInvestment | UTOPIA | COAL       | 1      | 2049 | 0         |
| TotalAnnualMaxCapacityInvestment | UTOPIA | COAL       | 1      | 2050 | 0         |

Note, that the `OPTION` column will dictate whether the option is made or not. For each
model run, either all data identifed as the `0` option or the `1` option will be used,
not both. There can be as many options as the modeller desires.

## `model`

This directory houses the reference GNU MathProg OSeMOSYS model you are using

## `results`

Contains CSV result files for each model run

## `src`

Contains all scripts

## `steps`

Solver outputs for each CSV model run. If using GLPK, these will be result CSV
files, if using a different solver, this will be a text file.

# Running Instructions

## Objective
Run a 5 step model, over the horizon of 1990 to 2010 that makes investment decesions
about allowing investment in coal.

## 1. Add the model file
Drop in an osemsosys file (called `osemosys.txt`) into the `model/` directory

## 2. Add the base data file
**NB:** Neither the model data nor the scenario data should make use of the parameter _TotalAnnualMaxCapacity_. It can cause problems when passing _NewCapacity_ from one step to the next step.

Drop in a MathProg formatted data file in the `data/` folder. The data file
can be long formatted (otoole) or wide formatted (momani)

## 3. Add in scenario data
For the first step, add the file `data/scenarios/1/A.csv`, where one
option allows investment in IMPHCO, and one options does not allow it.

|             PARAMETER            | REGION | TECHNOLOGY | OPTION | YEAR | VALUE     |
|:--------------------------------:|:------:|------------|--------|:----:|-----------|
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPHCO1    | 0      | 1990 | 999999999 |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPHCO1    | 0      | 1991 | 999999999 |
| ...                              | ...    | ...        | ...    | ...  | ...       |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPHCO1    | 0      | 2009 | 999999999 |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPHCO1    | 0      | 2010 | 999999999 |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPHCO1    | 1      | 1990 | 0         |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPHCO1    | 1      | 1991 | 0         |
| ...                              | ...    | ...        | ...    | ...  | ...       |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPHCO1    | 1      | 2009 | 0         |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPHCO1    | 1      | 2010 | 0         |

In this same step, but independent from the decision to invest in IMPHCO, we
want to also add the option to invest in importing uranium. Add the file
`data/scenarios/1/B.csv`

|             PARAMETER            | REGION | TECHNOLOGY | OPTION | YEAR | VALUE     |
|:--------------------------------:|:------:|------------|--------|:----:|-----------|
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPURN1    | 0      | 1990 | 999999999 |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPURN1    | 0      | 1991 | 999999999 |
| ...                              | ...    | ...        | ...    | ...  | ...       |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPURN1    | 0      | 2009 | 999999999 |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPURN1    | 0      | 2010 | 999999999 |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPURN1    | 1      | 1990 | 0         |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPURN1    | 1      | 1991 | 0         |
| ...                              | ...    | ...        | ...    | ...  | ...       |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPURN1    | 1      | 2009 | 0         |
| TotalAnnualMaxCapacityInvestment | UTOPIA | IMPURN1    | 1      | 2010 | 0         |

In the second step, through one decesion, we want to decide the allowable investment
in importing coal, importing RL1, and if RLu is allowed to run or not. Add the file
`data/scenarios/2/C.csv`

|             PARAMETER                   | REGION | TECHNOLOGY | OPTION | YEAR | VALUE     |
|:---------------------------------------:|:------:|------------|--------|:----:|-----------|
| TotalAnnualMaxCapacityInvestment        | UTOPIA | IMPHCO1    | 0      | 1990 | 999999999 |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | IMPHCO1    | 0      | 1991 | 999999999 |
| ...                                     | ...    | ...        | ...    | ...  | ...       |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | IMPHCO1    | 0      | 2009 | 999999999 |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | IMPHCO1    | 0      | 2010 | 999999999 |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | IMPHCO1    | 1      | 1990 | 0         |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | IMPHCO1    | 1      | 1991 | 0         |
| ...                                     | ...    | ...        | ...    | ...  | ...       |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | IMPHCO1    | 1      | 2009 | 0         |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | IMPHCO1    | 1      | 2010 | 0         |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | RL1        | 0      | 1990 | 9999999   |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | RL1        | 0      | 1991 | 9999999   |
| ...                                     | ...    | ...        | ...    | ...  | ...       |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | RL1        | 0      | 2009 | 9999999   |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | RL1        | 0      | 2010 | 9999999   |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | RL1        | 1      | 1990 | 0         |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | RL1        | 1      | 1991 | 0         |
| ...                                     | ...    | ...        | ...    | ...  | ...       |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | RL1        | 1      | 2009 | 0         |
| TotalAnnualMaxCapacityInvestment        | UTOPIA | RL1        | 1      | 2010 | 0         |
| TotalTechnologyAnnualActivityUpperLimit | UTOPIA | RLu        | 0      | 1990 | 9999999   |
| TotalTechnologyAnnualActivityUpperLimit | UTOPIA | RLu        | 0      | 1991 | 9999999   |
| ...                                     | ...    | ...        | ...    | ...  | ...       |
| TotalTechnologyAnnualActivityUpperLimit | UTOPIA | RLu        | 0      | 2009 | 9999999   |
| TotalTechnologyAnnualActivityUpperLimit | UTOPIA | RLu        | 0      | 2010 | 9999999   |
| TotalTechnologyAnnualActivityUpperLimit | UTOPIA | RLu        | 1      | 1990 | 0         |
| TotalTechnologyAnnualActivityUpperLimit | UTOPIA | RLu        | 1      | 1991 | 0         |
| ...                                     | ...    | ...        | ...    | ...  | ...       |
| TotalTechnologyAnnualActivityUpperLimit | UTOPIA | RLu        | 1      | 2009 | 0         |
| TotalTechnologyAnnualActivityUpperLimit | UTOPIA | RLu        | 1      | 2010 | 0         |

## 4. Run the workflow
```bash
cd src
python main_ms.py --step_length 5 --input_data ../data/<datafile_name>.txt
```

## 6. View Results
Under the results folder, there should now be results for all the
permutations of options.

For example, the results of implementing option 0 in scenario A, option 1 in
scenario B, and option 1 in scenario C are nested under the folder `results/1A0-1B1/2C1`.

```bash
OSeMOSYS_STEP
├── data
├── model
├── results
│   ├── 1A0-1B0
│   │   ├── 2C0
│   │   │   ├── *.csv
│   │   │   └── ...
│   │   └── 2C1
│   │       ├── *.csv
│   │       └── ...
│   ├── 1A0-1B1
│   │   ├── 2C0
│   │   │   ├── *.csv
│   │   │   └── ...
│   │   └── 2C1
│   │       ├── *.csv
│   │       └── ...
│   ├── 1A1-1B0
│   │   ├── 2C0
│   │   │   ├── *.csv
│   │   │   └── ...
│   │   └── 2C1
│   │       ├── *.csv
│   │       └── ...
│   └── 1A1-1B1
│       ├── 2C0
│       │   ├── *.csv
│       │   └── ...
│       └── 2C1
│           ├── *.csv
│           └── ...
├── src
└── steps
```

# Installation

You can use pip to install the package directly from Github:

    pip install git+https://github.com/KTH-dESA/OSeMOSYS_step.git@main#egg=osemosys_step

While in development phase, you can test this like so:

    pip install --dry-run git+https://github.com/KTH-dESA/OSeMOSYS_step.git@packaging#egg=osemosys_step

Or you install a development version like so:

    git clone https://github.com/KTH-dESA/OSeMOSYS_step.git osemosys_step
    cd osemosys_step
    pip install -e .

# Development

OSeMOSYS_step is packaged using [hatchling](https://hatch.pypa.io/latest/)

Create the development environment:

    hatch env create

Run the tests:

    hatch run test

Run linting for style, typing and format:

     hatch run lint:al

The version number is taken from the git tag.  Before building and publishing the package, you should create a new annotated tag.

First, check the previous tags:

    git tag

Then create a new annotated tag:

    git tag -a v1.0 -m "First full release of OSeMOSYS Step"

Build the package:

    hatch build

Publish the package to PyPI:

    hatch publish

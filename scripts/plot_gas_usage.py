#%%
import argparse
import json
import gzip
import logging
from os import path

import pandas as pd
from pandas.io.json import json_normalize
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA



COLUMNS_TO_CAST = [
    "transaction.gas",
    "transaction.gas_for_deposit",
    "transaction.gas_refunded",
    "transaction.gas_used",
]


def get_basename(filepath):
    basename = path.basename(filepath)
    while True:
        basename, ext = path.splitext(basename)
        if not ext:
            return basename


def normalize(X):
    return (X - X.mean()) / X.std()


def combine(X, Y):
    X = normalize(X)
    Y = normalize(Y)
    XY = np.stack([X, Y], axis=1)
    return PCA(n_components=1).fit_transform(XY)


def load_data(filepath, start=1_000_000, stop=1_500_000):
    logging.info("loading data from %s", filepath)
    rows = []
    with gzip.open(filepath) as f:
        for i, line in enumerate(f):
            if i >= stop:
                break
            elif i >= start:
                rows.append(json.loads(line))
    df = json_normalize(rows)
    for column in COLUMNS_TO_CAST:
        df[column] = df[column].astype(np.int64)
    logging.info("finished loading data from %s", filepath)
    return df


def plot_memory_graph(df, args):
    if args.max_memory:
        df = df[df["usage.extra_memory_allocated"] < args.max_memory]
    df["memory_intensive"] = df["usage.extra_memory_allocated"] > args.memory_threshold
    with_memory_allocated = df[df["usage.extra_memory_allocated"] >= 0]
    hue = "type" if "type" in df.columns else "memory_intensive"
    g = sns.lmplot(x="transaction.gas_used", y="usage.extra_memory_allocated",
                   data=with_memory_allocated, hue=hue,
                   scatter_kws=dict(rasterized=True))
    g.ax.set_xlabel("Gas used")
    g.ax.set_ylabel("Memory allocated (B)")
    g.ax.ticklabel_format(axis="both", style="sci", scilimits=(0, 5))
    output_path = args.output or "plots/memory-gas-{0}-{1}.pdf"
    plt.savefig(output_path.format(args.start, args.stop))


def plot_cpu_graph(df, args):
    if not args.include_dos:
        df = df[df["usage.clock_time"] < 1]
    hue = "type" if "type" in df.columns else None
    g = sns.lmplot(x="transaction.gas_used", y="usage.clock_time",
                   data=df, hue=hue,
                   scatter_kws=dict(rasterized=True))
    ax = g.ax
    # ax = sns.regplot(x="transaction.gas_used", y="usage.clock_time",
    #                  data=df,
    #                  scatter_kws=dict(rasterized=True))
    ax.set_xlabel("Gas used")
    ax.set_ylabel("Clock time (s)")
    ax.ticklabel_format(axis="both", style="sci", scilimits=(0, 5))
    output_path = args.output or "plots/cpu-gas-{0}-{1}.pdf"
    plt.savefig(output_path.format(args.start, args.stop))


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(prog="analyze-transactions")

    subparsers = parser.add_subparsers(dest="command")

    memory_parser = subparsers.add_parser("memory")
    memory_parser.add_argument("input", nargs="+", help="input file")
    memory_parser.add_argument("--output", help="output file")
    memory_parser.add_argument("--start", help="start index", type=int, default=1_000_000)
    memory_parser.add_argument("--stop", help="stop index", type=int, default=1_500_000)
    memory_parser.add_argument("--max-memory", help="max memory", type=int)
    memory_parser.add_argument("--memory-threshold", help="threshold for high memory", type=int, default=300_000)

    cpu_parser = subparsers.add_parser("cpu")
    cpu_parser.add_argument("input", nargs="+", help="input file")
    cpu_parser.add_argument("--output", help="output file")
    cpu_parser.add_argument("--start", help="start index", type=int, default=1_000_000)
    cpu_parser.add_argument("--stop", help="stop index", type=int, default=1_500_000)
    cpu_parser.add_argument("--include-dos", help="include dos data points",
                            default=False, action="store_true")

    args = parser.parse_args()

    if not args.command:
        parser.error("no command provided")

    if len(args.input) == 1:
        df = load_data(args.input[0], start=args.start, stop=args.stop)
    else:
        dfs = []
        for filepath in args.input:
            df = load_data(filepath, start=args.start, stop=args.stop)
            df["type"] = get_basename(filepath)
            dfs.append(df)
        df = pd.concat(dfs, ignore_index=True)


    if args.command == "memory":
        plot_memory_graph(df, args)
    elif args.command == "cpu":
        plot_cpu_graph(df, args)



#%%

if __name__ == "__main__":
    main()


#%%

MEASUREMENTS_PATH = "build/gas-measurements.jsonl.gz"

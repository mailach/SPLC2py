import os


def _extract_options(config: str):
    config = config.split('"')[1].split("%;%")
    config = [option for option in config if option != ""]
    return config


def extract_samples(cache_dir: str):
    with open(os.path.join(cache_dir, "sampled.txt"), "r", encoding="utf-8") as f:
        samples = f.readlines()
    configs = [_extract_options(config) for config in samples]
    return configs


def _generate_model(history):
    model = _find_best_model(history)
    terms = model["Model"].split("+")
    return [
        {
            "coefficient": float(t.split(" * ")[0]),
            "options": t.strip().split(" * ")[1:],
        }
        for t in terms
    ]


def _find_best_model(models):
    best = [float(models[0]["ValidationError"]), 0]
    for i in range(len(models)):
        if float(models[i]["ValidationError"]) < best[0]:
            best[0] = float(models[i]["ValidationError"])
            best[1] = i
    return models[best[1]]


def _time_to_sec(time_str):
    hours, mins, secs = time_str.split(":")
    return int(hours) * 60 * 60 + int(mins) * 60 + float(secs)


def _get_index(rows, str_to_search):
    return [i for i in range(len(rows)) if str_to_search in rows[i]][0]


def extract_model(tmpdir):
    with open(os.path.join(tmpdir, "logs.txt"), "r", encoding="utf-8") as f:
        logs = f.readlines()

    beginModels = logs.index("command: analyze-learning\n") + 1
    endModels = logs.index("Analyze finished\n")
    learning_time = _time_to_sec(logs[_get_index(logs, "Elapsed=")].split("=")[1])
    configs_with_to_large_dev = (
        logs[_get_index(logs, "large deviation:")].split(":")[1].strip()
    )
    table = logs[beginModels:endModels]
    header = [h.strip() for h in table[0].split(",")]
    history = []
    for row in table[3:]:
        row = row.split(";")
        m = {}
        for i in range(len(row)):
            m[header[i]] = row[i]
        history.append(m)

    return _generate_model(history), history, learning_time, configs_with_to_large_dev

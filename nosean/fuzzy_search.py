import re


class FuzzySearch:

    def __init__(self, entries: list[str]):
        self.entries = entries

    def fuzzy_search(self, query: str, max=5):
        new_var = ".*?".join(list(query))
        expr = f".*?{new_var}.*?"
        print(expr)
        regex = re.compile(expr)
        results = []
        for entry in self.entries:
            result = regex.search(entry.lower())
            if result:
                results.append((len(result.group()), result.start(), entry))
        return [x for  _, _, x in sorted(results)][:5]

if __name__ == "__main__":
    entries = [
        "README",
        "Computer Assisted Rehabilitation Environment",
        "Connectors",
        "D-Flow 3.36 Event Mapping Window",
        "D-Flow 3.36 MoCap Module",
        "D-Flow 3.36 Module Action",
        "D-Flow 3.36 Module",
        "D-Flow 3.36 Self-Definable Event",
        "D-Flow Application",
        "D-Flow Event System",
        "D-Flow Global Event",
        "D-Flow Pre-Defined Event",
        "D-Flow Runtime Subject Management",
        "Gait Real-time Analysis Interactive Lab",
        "Ganganalyse",
        "Human Body Model",
        "Module Reference Manual",
        "Motek D-Flow 3.36",
        "Motek Medical",
        "Phidget",
        "Segment",
        "Vicon Nexus",
        "Vicon",
        "VR",
        "Welcome",
    ]
    result = FuzzySearch(entries).fuzzy_search("dflow")
    print(result)

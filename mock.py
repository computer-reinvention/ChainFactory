from chainfactory import Engine

if __name__ == "__main__":
    haiku_engine = Engine.from_file("examples/haiku_purpose.fctr")
    res = haiku_engine(topic="Language Models", num=3)

    for haiku in res.haikus:
        print("Haiku:")
        print(haiku.haiku)
        print("Explanation:")
        print(haiku.explanation)
        print("\n")

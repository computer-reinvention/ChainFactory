import pendulum
from pprint import pprint
from src.types.factory import Factory
from src.interfaces.engine import ChainFactoryEngine


if __name__ == "__main__":
    engine = ChainFactoryEngine.from_file("chains/extract_datetimes.yaml")

    res = engine(
        {
            "current_dt": pendulum.now().to_day_datetime_string(),
            "text": "########################################\nInitial Email:\nHi Emma,\nCan we schedule a call to talk about our upcoming plans? I'm free (PST):\nAugust 3: 2pm-4pm\nAugust 5: 10am-12pm\nPlease let me know if either of these times work for you.\nBest,\nJames\n########################################\n",
        }
    )

    print("===========================")
    pprint(res.dict())
    print("===========================")

# ===========================================================================================
# Q. Can this chainlink correctly identify the cancellation intent in an email?             |
# -------------------------------------------------------------------------------------------
#                                                                                           |
# @chainlink cancel                                                                         |
# purpose: return true if a given input email explicitly contains a cancellation request    |
# in:                                                                                       |
# 	email_body: str                                                                         |
# out:                                                                                      |
#   is_cancellation_request: bool                                                          |
#                                                                                           |
# -------------------------------------------------------------------------------------------

from chainfactory import Engine, EngineConfig


def test_fn(path: str, **kwargs):
    """
    Function to test while developing.
    """
    res = engine(**kwargs)
    return res


EMAIL_WITH_CANCEL = """Hi John,

Hope you're doing well! I'm reaching out to let you know that I need to cancel our meeting scheduled for this Friday afternoon.

If you're open to it, we can set up another time that works for you. Let me know what's best!

Thanks for understanding.

Best,
Jane
jane.doe@email.com
(555) 123-4567
"""

EMAIL_SANS_CANCEL = """Hi Alex,

I hope this message finds you well. I wanted to touch base regarding our upcoming meeting scheduled for Thursday, October 19th at 3:00 PM. There have been some recent developments that might impact our agenda, and I thought it would be valuable for us to discuss any potential schedule adjustments that could accommodate all parties involved.

If you have any thoughts or preferences around this, please feel free to share them. I believe ensuring everyone's availability will enhance our discussions and outcomes.

Looking forward to your input.

Best regards,  
Jordan
"""


if __name__ == "__main__":
    config = EngineConfig(pause_between_executions=True)
    engine = Engine.from_file("examples/email.fctr", config=config)

    should_be_true = engine(email_body=EMAIL_WITH_CANCEL).is_cancellation_request
    assert should_be_true

    should_be_false = engine(email_body=EMAIL_SANS_CANCEL).is_cancellation_request
    assert not should_be_false

    print("All is well.")

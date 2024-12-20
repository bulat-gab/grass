from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    THREADS: int = 5  # for register account / claim rewards mode / approve email mode
    MIN_PROXY_SCORE: int = 50  # Put MIN_PROXY_SCORE = 0 not to check proxy score (if site is down)

    USE_CONSOLE_VERSION: bool = True # if True - use console version and no interface shows
    NODE_TYPE: str = "2x"  # 1x, 1_25x, 2x   

    #########################################
    APPROVE_EMAIL: bool = False # approve email (NEEDED IMAP AND ACCESS TO EMAIL)
    CONNECT_WALLET: bool = False # connect wallet (put private keys in wallets.txt)
    SEND_WALLET_APPROVE_LINK_TO_EMAIL: bool = False # send approve link to email
    APPROVE_WALLET_ON_EMAIL: bool = False # get approve link from email (NEEDED IMAP AND ACCESS TO EMAIL)
    SEMI_AUTOMATIC_APPROVE_LINK: bool = False # if True - allow to manual paste approve link from email to cli
    # If you have possibility to forward all approve mails to single IMAP address:
    SINGLE_IMAP_ACCOUNT: str = "" # usage "name@domain.com:password"

    # skip for auto chosen
    EMAIL_FOLDER: str = ""  # folder where mails comes (example: SPAM INBOX JUNK etc.)
    IMAP_DOMAIN: str = ""  # imap server domain (example: imap.firstmail.ltd for firstmail)

    #########################################
    CLAIM_REWARDS_ONLY: bool = False # claim tiers rewards only (https://app.getgrass.io/dashboard/referral-program)

    STOP_ACCOUNTS_WHEN_SITE_IS_DOWN: bool = True  # stop account for 20 minutes, to reduce proxy traffic usage
    CHECK_POINTS: bool = True  # show point for each account every nearly 10 minutes
    SHOW_LOGS_RARELY: bool = False # not always show info about actions to decrease pc influence

    # Mining mode
    MINING_MODE: bool = True  # False - not mine grass, True - mine grass | Remove all True on approve \ register section

    # REGISTER PARAMETERS ONLY
    REGISTER_ACCOUNT_ONLY: bool = False
    REGISTER_DELAY: tuple = (3, 7)

    TWO_CAPTCHA_API_KEY: str = ""
    ANTICAPTCHA_API_KEY: str = ""
    CAPMONSTER_API_KEY: str = ""
    CAPSOLVER_API_KEY: str = ""
    CAPTCHAAI_API_KEY: str = ""

    # Use proxy also for mail handling
    USE_PROXY_FOR_IMAP: bool = False

    # Captcha params, left empty
    CAPTCHA_PARAMS: dict = {
        "captcha_type": "v2",
        "invisible_captcha": False,
        "sitekey": "6LeeT-0pAAAAAFJ5JnCpNcbYCBcAerNHlkK4nm6y",
        "captcha_url": "https://app.getgrass.io/register"
    }

    ########################################

    ACCOUNTS_FILE_PATH: str = "data/accounts.txt"
    PROXIES_FILE_PATH: str = "data/proxies.txt"
    WALLETS_FILE_PATH: str = "data/wallets.txt"
    PROXY_DB_PATH: str = 'data/proxies_stats.db'

settings = Settings()
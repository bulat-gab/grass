import asyncio
import ctypes
import os
import random
import sys
import traceback

import aiohttp
from art import text2art
from imap_tools import MailboxLoginError
from termcolor import colored, cprint

from better_proxy import Proxy

from core import Grass
from core.autoreger import AutoReger
from core.utils import logger, file_to_list
from core.utils.accounts_db import AccountsDB
from core.utils.exception import EmailApproveLinkNotFoundException, LoginException, RegistrationException
from core.utils.generate.person import Person
from data.config import settings
from data import database


def bot_info(name: str = ""):
    cprint(text2art(name), 'green')

    if sys.platform == 'win32':
        ctypes.windll.kernel32.SetConsoleTitleW(f"{name}")

    print(
        f"{colored('EnJoYeR <crypto/> moves:', color='light_yellow')} "
        f"{colored('https://t.me/+tdC-PXRzhnczNDli', color='light_green')}"
    )


async def worker_task(_id, account: str, proxy: str = None, wallet: str = None, db: AccountsDB = None):
    consumables = account.split(" 🚀 ")[:3]
    imap_pass = None
    
    if settings.SINGLE_IMAP_ACCOUNT:
        consumables.append(settings.SINGLE_IMAP_ACCOUNT.split(" 🚀 ")[1])

    if len(consumables) == 1:
        email = consumables[0]
        password = Person().random_string(8)
    elif len(consumables) == 2:
        email, password = consumables
    else:
        email, password, imap_pass = consumables

    grass = None

    try:
        grass = Grass(_id, email, password, proxy, db)

        if settings.MINING_MODE:
            await asyncio.sleep(random.uniform(1, 2) * _id)
        else:
            await asyncio.sleep(random.uniform(*settings.REGISTER_DELAY))
        
        logger.info(f"Starting #{_id} | {email} | {proxy}")

        if settings.REGISTER_ACCOUNT_ONLY:
            await grass.create_account()
        elif settings.APPROVE_EMAIL or settings.CONNECT_WALLET or settings.SEND_WALLET_APPROVE_LINK_TO_EMAIL or settings.APPROVE_WALLET_ON_EMAIL:
            await grass.enter_account()

            user_info = await grass.retrieve_user()

            if settings.APPROVE_EMAIL:
                if user_info['result']['data'].get("isVerified"):
                    logger.info(f"{grass.id} | {grass.email} email already verified!")
                else:
                    if settings.SEMI_AUTOMATIC_APPROVE_LINK:
                        imap_pass = "placeholder"
                    elif imap_pass is None:
                        raise TypeError("IMAP password is not provided")
                    await grass.confirm_email(imap_pass)
            if settings.CONNECT_WALLET:
                if user_info['result']['data'].get("walletAddress"):
                    logger.info(f"{grass.id} | {grass.email} wallet already linked!")
                else:
                    await grass.link_wallet(wallet)

            if user_info['result']['data'].get("isWalletAddressVerified"):
                logger.info(f"{grass.id} | {grass.email} wallet already verified!")
            else:
                if settings.SEND_WALLET_APPROVE_LINK_TO_EMAIL:
                    await grass.send_approve_link(endpoint="sendWalletAddressEmailVerification")
                if settings.APPROVE_WALLET_ON_EMAIL:
                    if settings.SEMI_AUTOMATIC_APPROVE_LINK:
                        imap_pass = "placeholder"
                    elif imap_pass is None:
                        raise TypeError("IMAP password is not provided")
                    await grass.confirm_wallet_by_email(imap_pass)
        elif settings.CLAIM_REWARDS_ONLY:
            await grass.claim_rewards()
        else:
            await grass.start()

        return True
    except (LoginException, RegistrationException) as e:
        logger.warning(f"{_id} | {e}")
    except MailboxLoginError as e:
        logger.error(f"{_id} | {e}")
    # except NoProxiesException as e:
    #     logger.warning(e)
    except EmailApproveLinkNotFoundException as e:
        logger.warning(e)
    except aiohttp.ClientError as e:
        logger.warning(f"{_id} | Some connection error: {e}...")
    except Exception as e:
        logger.error(f"{_id} | not handled exception | error: {e} {traceback.format_exc()}")
    finally:
        if grass:
            await grass.session.close()
            # await grass.ws_session.close()


async def main():
    accounts = file_to_list(settings.ACCOUNTS_FILE_PATH)

    if not accounts:
        logger.warning("No accounts found!")
        return

    proxies = [Proxy.from_str(proxy).as_url for proxy in file_to_list(settings.PROXIES_FILE_PATH)]

    #### delete DB if it exists to clean up
    if os.path.exists(settings.PROXY_DB_PATH):
        os.remove(settings.PROXY_DB_PATH)

    db_path = "do_not_commit.data/grass_db.sqlite3"
    if os.path.exists(db_path):
        os.remove(db_path)

    db = AccountsDB(settings.PROXY_DB_PATH)
    await db.connect()
    await database.initialize_database()

    for i, account in enumerate(accounts):
        account = account.split(" 🚀 ")[0]
        proxy = proxies[i] if len(proxies) > i else None

        if await db.proxies_exist(proxy) or not proxy:
            continue

        await db.add_account(account, proxy)
        await database.User.add(email=account)
        await database.Proxy.add(url=proxy)
        await database.Device.add(account, proxy)

    await db.delete_all_from_extra_proxies()
    await db.push_extra_proxies(proxies[len(accounts):])
    for p in proxies[len(accounts):]:
        await database.Proxy.add(url=proxy)

    autoreger = AutoReger.get_accounts(
        (settings.ACCOUNTS_FILE_PATH, settings.PROXIES_FILE_PATH, settings.WALLETS_FILE_PATH),
        with_id=True,
        static_extra=(db,)
    )

    threads = settings.THREADS

    if settings.REGISTER_ACCOUNT_ONLY:
        msg = "__REGISTER__ MODE"
    elif settings.APPROVE_EMAIL or settings.CONNECT_WALLET or settings.SEND_WALLET_APPROVE_LINK_TO_EMAIL or settings.APPROVE_WALLET_ON_EMAIL:
        if settings.CONNECT_WALLET:
            wallets = file_to_list(settings.WALLETS_FILE_PATH)
            if len(wallets) == 0:
                logger.error("Wallet file is empty")
                return
            elif len(wallets) != len(accounts):
                logger.error("Wallets count != accounts count")
                return
        elif len(accounts[0].split(" 🚀 ")) != 3:
            logger.error("For __APPROVE__ mode: Need to provide email, password and imap password - email 🚀 password 🚀 imap_password")
            return

        msg = "__APPROVE__ MODE"
    elif settings.CLAIM_REWARDS_ONLY:
        msg = "__CLAIM__ MODE"
    else:
        msg = "__MINING__ MODE"
        threads = len(autoreger.accounts)

    logger.info(msg)

    await autoreger.start(worker_task, threads)

    await db.close_connection()


if __name__ == "__main__":
    bot_info("GRASS_AUTO")

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())

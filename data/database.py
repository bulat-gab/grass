
from datetime import datetime
from typing import Optional
from tortoise import Model, Tortoise, fields
from tortoise.transactions import atomic

from tortoise.functions import Sum, Max
from tortoise.exceptions import IntegrityError

from core.utils import logger

class Account(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, null=False)
    # user_id = fields.CharField(max_length=255, null=True)
    # access_token = fields.TextField(null=True)
    proxies = fields.ReverseRelation["Proxy"]  # One-to-Many relationship with Proxy

    def __str__(self):
        return f"{self.id} | {self.email}"

    class Meta:
        table = "Accounts"

    @classmethod
    async def get_account(cls, email: str):
        return await cls.get_or_none(email=email)

    @classmethod
    async def get_accounts(cls):
        return await cls.all()

    @classmethod
    @atomic()
    async def add_account(cls, email: str, new_proxy: str) -> bool:
        """
        Add a proxy to an existing account or create a new account.
        
        Args:
            email (str): The email of the account.
            new_proxy (str): The URL of the new proxy.

        Returns:
            bool: True if the proxy was successfully added, False otherwise.
        """
        if not new_proxy:
            return False

        existing_proxy = await Proxy.filter(url=new_proxy).first()
        if existing_proxy:
            logger.warning(f"Proxy '{new_proxy}' is already assigned.")
            return False

        account, created = await cls.get_or_create(email=email)

        if created:
            logger.debug(f"Created new account for email '{email}'.")

        try:
            await Proxy.create(url=new_proxy, account=account)
            logger.debug(f"Added proxy '{new_proxy}' to account '{email}'.")
            return True
        except IntegrityError:
            logger.error(f"Failed to add proxy '{new_proxy}' to account '{email}'.")
            return False
    
    @classmethod
    async def get_proxies_by_email(cls, email: str) -> list[str]:
        """
        Retrieve proxies associated with a given email.
        
        Args:
            email (str): The email of the account.

        Returns:
            list[str]: List of proxy URLs associated with the account.
        """
        account = await cls.get_or_none(email=email)

        if account:
            proxies = await Proxy.filter(account=account).values_list("url", flat=True)
            return proxies
        
        return []
    
class Proxy(Model):
    id = fields.IntField(pk=True)
    url = fields.CharField(max_length=255, unique=True)
    account: Optional["Account"] = fields.ForeignKeyField("models.Account", related_name="proxies", on_delete=fields.CASCADE)

    class Meta:
        table = "Proxies"
        unique_together = (("url", "account"),)

    def __str__(self):
        return f"{self.url}"

    @classmethod
    async def proxies_exist(cls, proxy_url: str) -> str | bool:
        """
        Check if a proxy exists in the database, and return the associated email if found.
        
        Args:
            proxy_url (str): The URL of the proxy to check.

        Returns:
            str | bool: The email of the associated account if the proxy exists, False otherwise.
        """
        proxy = await cls.filter(url=proxy_url).select_related("account").first()
        if proxy:
            logger.debug(f"Proxy '{proxy_url}' exists and is associated with email '{proxy.account.email}'")
            return proxy.account.email
        
        logger.debug(f"Proxy '{proxy_url}' does not exist")
        return False

class ExtraProxy(Model):
    id = fields.IntField(pk=True)
    proxy = fields.TextField()

    class Meta:
        table = "ExtraProxy"


    @classmethod
    @atomic()
    async def get_new_from_extra_proxies(cls) -> str | None:
        """
        Fetch the newest proxy from ProxyList, delete it, and return it.
        """
        # Get the latest proxy
        latest_proxy = await cls.filter().order_by("-id").first()

        if not latest_proxy:
            return None

        proxy_value = latest_proxy.proxy
        await latest_proxy.delete()
        return proxy_value


    @classmethod
    async def push_extra_proxies(cls, proxies: list[str]) -> None:
        """
        Insert multiple proxies into the ProxyList table.
        """
        # Create a list of ProxyList instances for bulk insertion
        proxy_instances = [cls(proxy=proxy) for proxy in proxies]

        # Bulk insert proxies into the table
        await cls.bulk_create(proxy_instances)

    @classmethod
    async def delete_all_from_extra_proxies(cls) -> None:
        """
        Delete all proxies from the ProxyList table.
        """
        # Delete all entries from the ProxyList table
        await cls.all().delete()

class PointStats(Model):
    id = fields.IntField(pk=True)
    email = fields.TextField()
    points = fields.FloatField()

    class Meta:
        table = "PointStats"

    @classmethod
    @atomic()
    async def update_or_create_point_stat(cls, user_id, email, points: str):
        float_points = float(points)

        point_stat = await cls.get_or_none(id=user_id)
        if point_stat:
            point_stat.email = email
            point_stat.points = float_points
            await point_stat.save()

        else:
            await cls.create(id=user_id, email=email, points=float_points)


    @classmethod
    async def get_total_points(cls):
        """
        Calculate the total of the maximum points for each email.
        """
        # Annotate to get the maximum points per email
        max_points_per_email = await cls.annotate(max_points=Max("points")).group_by("email").all()

        # Sum the maximum points across all emails
        total_points = sum(record.max_points for record in max_points_per_email)

        return total_points
    

class LoginData(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=False)
    user_id = fields.CharField(max_length=255, unique=False)
    browser_id = fields.CharField(max_length=255, unique=True)
    access_token = fields.TextField()

    class Meta:
        table = "LoginData"

    @classmethod
    async def get_login_data(cls, email: str, browser_id: str) -> Optional["LoginData"]:
        return await cls.get_or_none(email=email, browser_id=browser_id)

    # @classmethod
    # async def get_by_user_id(cls, user_id: str, browser_id: str) -> Optional["LoginData"]:
    #     return await cls.get_or_none(user_id=user_id, browser_id=browser_id)

    @classmethod
    async def add(cls, email: str, user_id: str, browser_id: str, access_token: str):
        login_data, created = await cls.get_or_create(email=email, user_id=user_id, browser_id=browser_id, access_token=access_token)
        if created:
            logger.info(f"{email} | Login data added")

    @classmethod
    async def create_if_not_exist(cls, email: str):
        account_data, created = await cls.get_or_create(email=email)
        if created:
            logger.debug(f"New row added to LoginData: '{email}'")


    @classmethod
    async def set_user_id(cls, email: str, user_id: str):
        account_data = await cls.get_or_none(email=email)
        if not account_data:
            logger.debug(f"LoginData not found: '{email}'")
            return False

        account_data.user_id = user_id
        await account_data.save()
        return True
    
    @classmethod
    async def set_access_token(cls, email: str, access_token: str):
        account_data = await cls.get_or_none(email=email)
        if not account_data:
            logger.debug(f"LoginData not found: '{email}'")
            return False

        account_data.access_token = access_token
        await account_data.save()
        return True


async def initialize_database() -> None:
    db_url='sqlite://data/grass_db.sqlite3'

    try:
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["data.database"]},
            timezone="UTC",
        )

        await Tortoise.generate_schemas(safe=True)

    except Exception as error:
        logger.error(f"Error while initializing database: {error}")
        exit(0)


async def clean() -> None:
    """
    Delete all from: Accounts, Proxies, ExtraProxy, PointStats.

    Keep only LoginData
    """
    await Proxy.all().delete()
    await Account.all().delete()
    await ExtraProxy.all().delete()
    await PointStats.all().delete()
import requests
import time
import asyncio
import aiohttp
from uuid import uuid4
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from aws.repositories.exchange_repository import ExchangeRepository
from aws.repositories.platform_repository import PlatformRepository
from aws.repositories.token_repository import TokensRepository
from aws.repositories.token_stats_repository import TokenStatsRepository
from aws.repositories.exchanges_stats_repository import ExchangesStatsRepository
from configs.config import settings
from models.exchanges import Exchange
from models.platform import Platform
from models.tokens import Token
from models.token_stats import TokenStats
from models.exchanges_stats import ExchangesStats


class CoingeckoAggregator:
    BASE_URL = "https://api.coingecko.com/api/v3"
    PRO_BASE_URL = "https://pro-api.coingecko.com/api/v3"

    def __init__(self, 
                 api_key: str = settings.Coingecko.API_KEY, 
                 demo_key: str = settings.Coingecko.TEST_API_KEY,
                 is_demo: bool = True):
        
        self.base_url = self.BASE_URL if is_demo else self.PRO_BASE_URL
        self.api_key = demo_key if is_demo else api_key
        self.headers = {
            "Accepts": "application/json",
            "X-Cg-Pro-Api-Key": self.api_key
        }
        
        self.token_repo = TokensRepository()
        self.platform_repo = PlatformRepository()
        self.exchange_repo = ExchangeRepository()
        self.token_stats_repo = TokenStatsRepository()
        self.exchanges_stats_repo = ExchangesStatsRepository()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None

    async def _make_async_request(self, session: aiohttp.ClientSession, endpoint: str, params: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}/{endpoint}"
        try:
            async with session.get(url, headers=self.headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except:
            return None

    def get_coins_markets(self, limit: int = 500) -> List[Dict]:
        all_coins = []
        per_page = min(250, limit)
        pages_needed = (limit + per_page - 1) // per_page
        
        for page in range(1, pages_needed + 1):
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': per_page,
                'page': page,
                'sparkline': 'false',
                'price_change_percentage': '1h,24h,7d,30d'
            }
            
            data = self._make_request("coins/markets", params)
            if data:
                all_coins.extend(data)
            
            if len(all_coins) >= limit:
                break
                
        return all_coins[:limit]

    def get_exchanges_list(self, limit: int = 100) -> List[Dict]:
        params = {
            'per_page': min(250, limit),
            'page': 1
        }
        
        data = self._make_request("exchanges", params)
        return data[:limit] if data else []

    def get_coin_details(self, coin_id: str) -> Optional[Dict]:
        params = {
            'localization': 'false',
            'tickers': 'false',
            'market_data': 'true',
            'community_data': 'false',
            'developer_data': 'false',
            'sparkline': 'false'
        }
        return self._make_request(f"coins/{coin_id}", params)

    async def get_coin_details_async(self, session: aiohttp.ClientSession, coin_id: str) -> Optional[Dict]:
        params = {
            'localization': 'false',
            'tickers': 'false',
            'market_data': 'true',
            'community_data': 'false',
            'developer_data': 'false',
            'sparkline': 'false'
        }
        return await self._make_async_request(session, f"coins/{coin_id}", params)

    def get_exchange_details(self, exchange_id: str) -> Optional[Dict]:
        return self._make_request(f"exchanges/{exchange_id}")

    async def get_exchange_details_async(self, session: aiohttp.ClientSession, exchange_id: str) -> Optional[Dict]:
        return await self._make_async_request(session, f"exchanges/{exchange_id}")

    def update_tokens_stats_every_10_seconds(self, limit: int = 500) -> None:
        print(f"Updating TokenStats from markets data (limit: {limit})...")
        start_time = time.time()

        market_coins = self.get_coins_markets(limit)
        if not market_coins:
            print("No market data received")
            return

        print(f"Received {len(market_coins)} tokens in {time.time() - start_time:.2f}s")

        process_start = time.time()
        updated_count = 0
        failed_count = 0

        stats_batch = []
        for market_coin in market_coins:
            try:
                stats = self._create_token_stats_from_market(market_coin)
                if stats:
                    stats_batch.append(stats)
                    updated_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                if failed_count <= 5:
                    print(f"Error processing {market_coin.get('symbol', 'unknown')}: {e}")

        batch_start = time.time()
        saved_count = 0
        for stats in stats_batch:
            try:
                self.token_stats_repo.create_or_update(stats)
                saved_count += 1
            except Exception as e:
                print(f"Error saving {stats.symbol}: {e}")

        total_time = time.time() - start_time
        process_time = batch_start - process_start
        save_time = time.time() - batch_start

        print(f"Completed: {saved_count} saved, {failed_count} failed")
        print(f"Timing: Total {total_time:.2f}s (Process: {process_time:.2f}s, Save: {save_time:.2f}s)")

    def update_exchanges_stats_every_10_seconds(self, limit: int = 100) -> None:
        print(f"Updating ExchangesStats from list data (limit: {limit})...")
        start_time = time.time()
        
        exchanges_list = self.get_exchanges_list(limit)
        if not exchanges_list:
            print("No exchanges data received")
            return
        
        print(f"Received {len(exchanges_list)} exchanges in {time.time() - start_time:.2f}s")
        
        updated_count = 0
        failed_count = 0
        
        for exchange_data in exchanges_list:
            try:
                self._save_exchange_stats_from_list(exchange_data)
                updated_count += 1
            except Exception as e:
                failed_count += 1
                if failed_count <= 3:
                    print(f"Error processing {exchange_data.get('name', 'unknown')}: {e}")
        
        total_time = time.time() - start_time
        print(f"Completed: {updated_count} updated, {failed_count} failed in {total_time:.2f}s")

    async def collect_tokens_detailed_info_daily_async(self, limit: int = 500) -> None:
        print(f"Collecting detailed info for tokens (daily task, limit: {limit})...")
        start_time = time.time()
        
        all_token_stats = self.token_stats_repo.get_all()
        coingecko_ids = list(set([ts.get('coingecko_id') for ts in all_token_stats if ts.get('coingecko_id')]))
        
        if not coingecko_ids:
            print("No tokens found in TokenStats")
            return
        
        print(f"Found {len(coingecko_ids)} unique tokens to process")
        saved_count = 0
        failed_count = 0
        total_to_process = min(len(coingecko_ids), limit)
        coingecko_ids = coingecko_ids[:limit]
        
        batch_size = 50
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(coingecko_ids), batch_size):
                batch = coingecko_ids[i:i + batch_size]
                tasks = [self._save_token_detailed_info_async(session, coin_id) for coin_id in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if result and not isinstance(result, Exception):
                        saved_count += 1
                    else:
                        failed_count += 1
                
                if (i + batch_size) % 100 == 0 or (i + batch_size) >= len(coingecko_ids):
                    elapsed = time.time() - start_time
                    processed = min(i + batch_size, len(coingecko_ids))
                    rate = processed / elapsed if elapsed > 0 else 0
                    eta = (total_to_process - processed) / rate if rate > 0 else 0
                    print(f"Progress: {processed}/{total_to_process} ({rate:.1f}/s, ETA: {eta:.0f}s)")
                
                await asyncio.sleep(0.5)

        total_time = time.time() - start_time
        print(f"Completed in {total_time:.2f}s: {saved_count} saved, {failed_count} failed")

    async def collect_exchanges_detailed_info_daily_async(self, limit: int = 100) -> None:
        print(f"Collecting detailed info for exchanges (daily task, limit: {limit})...")
        start_time = time.time()
        
        all_exchange_stats = self.exchanges_stats_repo.get_all()
        exchange_names = list(set([es.get('name') for es in all_exchange_stats if es.get('name')]))
        
        if not exchange_names:
            print("No exchanges found in ExchangeStats")
            return
        
        print(f"Found {len(exchange_names)} exchanges to process")
        saved_count = 0
        failed_count = 0
        batch_size = 20
        exchange_names = exchange_names[:limit]
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(exchange_names), batch_size):
                batch = exchange_names[i:i + batch_size]
                tasks = []
                
                for exchange_name in batch:
                    exchange_id = self._name_to_id(exchange_name)
                    tasks.append(self._save_exchange_detailed_info_async(session, exchange_id))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if result and not isinstance(result, Exception):
                        saved_count += 1
                    else:
                        failed_count += 1
                
                processed = min(i + batch_size, len(exchange_names))
                print(f"Processed {processed}/{len(exchange_names)} exchanges")
                
                await asyncio.sleep(0.5)

        total_time = time.time() - start_time
        print(f"Successfully saved detailed info for {saved_count} exchanges in {total_time:.2f}s, {failed_count} failed")

    def collect_tokens_detailed_info_daily(self, limit: int = 500) -> None:
        asyncio.run(self.collect_tokens_detailed_info_daily_async(limit))

    def collect_exchanges_detailed_info_daily(self, limit: int = 100) -> None:
        asyncio.run(self.collect_exchanges_detailed_info_daily_async(limit))

    def _calculate_tvl(self, market_data: Dict) -> Optional[str]:
        try:
            market_cap = market_data.get('market_cap', {}).get('usd')
            total_volume = market_data.get('total_volume', {}).get('usd')
            circulating_supply = market_data.get('circulating_supply')
            current_price = market_data.get('current_price', {}).get('usd')
            
            if market_cap and total_volume and circulating_supply and current_price:
                velocity = total_volume / market_cap if market_cap > 0 else 0
                tvl_factor = max(0.1, min(2.0, 1 / (1 + velocity * 10)))
                estimated_tvl = market_cap * tvl_factor * 0.3
                return str(round(estimated_tvl, 2))
                
            return None
        except:
            return None

    def _create_token_stats_from_market(self, market_coin: Dict) -> Optional[TokenStats]:
        try:
            symbol = market_coin.get('symbol', '').upper()
            coingecko_id = market_coin.get('id')

            if not symbol or not coingecko_id:
                return None

            market_cap_usd = market_coin.get('market_cap')
            volume_24h_usd = market_coin.get('total_volume')
            liquidity_score = None

            if market_cap_usd and volume_24h_usd and market_cap_usd > 0:
                liquidity_score = str(round((volume_24h_usd / market_cap_usd) * 100, 4))

            tvl = self._calculate_tvl_from_market(market_coin)

            return TokenStats(
                symbol=symbol,
                coingecko_id=coingecko_id,
                coin_name=market_coin.get('name', ''),
                price=self._safe_str(market_coin.get('current_price')),
                market_cap=self._safe_str(market_cap_usd),
                trading_volume_24h=self._safe_str(volume_24h_usd),
                token_max_supply=self._safe_str(market_coin.get('max_supply')),
                token_total_supply=self._safe_str(market_coin.get('total_supply')),
                transactions_count_30d=self._safe_str(market_coin.get('market_cap_rank')),
                volume_1m_change_1m=self._safe_str(market_coin.get('price_change_percentage_30d_in_currency')),
                volume_24h_change_24h=self._safe_str(market_coin.get('price_change_percentage_24h')),
                ath=self._safe_str(market_coin.get('ath')),
                atl=self._safe_str(market_coin.get('atl')),
                liquidity_score=liquidity_score,
                tvl=tvl
            )
        except Exception:
            return None

    def _calculate_tvl_from_market(self, market_coin: Dict) -> Optional[str]:
        try:
            market_cap = market_coin.get('market_cap')
            total_volume = market_coin.get('total_volume')
            circulating_supply = market_coin.get('circulating_supply')
            current_price = market_coin.get('current_price')
            
            if market_cap and total_volume and circulating_supply and current_price:
                velocity = total_volume / market_cap if market_cap > 0 else 0
                tvl_factor = max(0.1, min(2.0, 1 / (1 + velocity * 10)))
                estimated_tvl = market_cap * tvl_factor * 0.3
                return str(round(estimated_tvl, 2))
                
            return None
        except:
            return None

    def _save_exchange_stats_from_list(self, exchange_data: Dict) -> None:
        try:
            exchange_id = exchange_data.get('id')
            if not exchange_id:
                return
            
            existing_exchange = self.exchange_repo.get_by_name(exchange_data.get('name'))
            db_exchange_id = existing_exchange['id'] if existing_exchange else exchange_id

            stats = ExchangesStats(
                exchange_id=db_exchange_id,
                name=exchange_data.get('name'),
                trading_volume_24h=self._safe_str(exchange_data.get('trade_volume_24h_btc')),
                trading_volume_1w=self._safe_str(exchange_data.get('trade_volume_24h_btc_normalized')),
                trading_volume_1m=self._safe_str(exchange_data.get('trade_volume_24h_btc_normalized')),
                visitors_30d=self._safe_str(exchange_data.get('trust_score')),
                coins_count=exchange_data.get('tickers_count', 0),
                reserves=self._safe_str(exchange_data.get('year_established'))
            )
            
            self.exchanges_stats_repo.create_or_update(stats)
            
        except Exception:
            pass

    async def _save_token_detailed_info_async(self, session: aiohttp.ClientSession, coingecko_id: str) -> Optional[Dict]:
        coin_details = await self.get_coin_details_async(session, coingecko_id)
        if not coin_details:
            return None

        try:
            links = coin_details.get('links', {})
            
            token = Token(
                name=coin_details.get('name'),
                coingecko_id=coin_details.get('id'),
                symbol=coin_details.get('symbol', '').upper(),
                description=self._get_description(coin_details.get('description', {})),
                website=self._get_first_link(links.get('homepage', [])),
                twitter=self._format_twitter_link(links.get('twitter_screen_name')),
                facebook=self._format_facebook_link(links.get('facebook_username')),
                reddit=links.get('subreddit_url'),
                repo_link=self._get_first_link(links.get('repos_url', {}).get('github', [])),
                avatar_image=coin_details.get('image', {}).get('large'),
                instagram=self._format_instagram_link(links.get('instagram_username')),
                discord=links.get('discord'),
                whitelabel_link=self._get_first_link(links.get('whitepaper', []))
            )
            
            saved_token = self.token_repo.create_if_not_exists(token)
            
            platforms = coin_details.get('platforms', {})
            for platform_name, address in platforms.items():
                if address and address.strip():
                    platform = Platform(
                        token_id=saved_token['id'],
                        name=platform_name,
                        token_address=address
                    )
                    self.platform_repo.create_if_not_exists(platform)
            
            return saved_token
        except Exception:
            return None

    def _save_token_detailed_info(self, coingecko_id: str) -> Optional[Dict]:
        coin_details = self.get_coin_details(coingecko_id)
        if not coin_details:
            return None

        try:
            links = coin_details.get('links', {})
            
            token = Token(
                name=coin_details.get('name'),
                coingecko_id=coin_details.get('id'),
                symbol=coin_details.get('symbol', '').upper(),
                description=self._get_description(coin_details.get('description', {})),
                website=self._get_first_link(links.get('homepage', [])),
                twitter=self._format_twitter_link(links.get('twitter_screen_name')),
                facebook=self._format_facebook_link(links.get('facebook_username')),
                reddit=links.get('subreddit_url'),
                repo_link=self._get_first_link(links.get('repos_url', {}).get('github', [])),
                avatar_image=coin_details.get('image', {}).get('large'),
                instagram=self._format_instagram_link(links.get('instagram_username')),
                discord=links.get('discord'),
                whitelabel_link=self._get_first_link(links.get('whitepaper', []))
            )
            
            saved_token = self.token_repo.create_if_not_exists(token)
            
            platforms = coin_details.get('platforms', {})
            for platform_name, address in platforms.items():
                if address and address.strip():
                    platform = Platform(
                        token_id=saved_token['id'],
                        name=platform_name,
                        token_address=address
                    )
                    self.platform_repo.create_if_not_exists(platform)
            
            return saved_token
        except Exception:
            return None

    async def _save_exchange_detailed_info_async(self, session: aiohttp.ClientSession, exchange_id: str) -> Optional[Dict]:
        try:
            exchange_details = await self.get_exchange_details_async(session, exchange_id)
            if not exchange_details:
                return None
            
            exchange = Exchange(
                name=exchange_details.get('name'),
                description=exchange_details.get('description'),
                website=exchange_details.get('url'),
                facebook=exchange_details.get('facebook_url'),
                reddit=exchange_details.get('reddit_url'),
                twitter=self._format_twitter_handle(exchange_details.get('twitter_handle')),
                avatar_image=exchange_details.get('image'),
                trading_pairs_count=exchange_details.get('trade_volume_24h_btc_normalized'),
                native_token_symbol=exchange_details.get('native_coin_id')
            )
            
            saved_exchange = self.exchange_repo.create_if_not_exists(exchange)
            return saved_exchange
            
        except Exception:
            return None

    def _save_exchange_detailed_info(self, exchange_id: str) -> Optional[Dict]:
        try:
            exchange_details = self.get_exchange_details(exchange_id)
            if not exchange_details:
                return None
            
            exchange = Exchange(
                name=exchange_details.get('name'),
                description=exchange_details.get('description'),
                website=exchange_details.get('url'),
                facebook=exchange_details.get('facebook_url'),
                reddit=exchange_details.get('reddit_url'),
                twitter=self._format_twitter_handle(exchange_details.get('twitter_handle')),
                avatar_image=exchange_details.get('image'),
                trading_pairs_count=exchange_details.get('trade_volume_24h_btc_normalized'),
                native_token_symbol=exchange_details.get('native_coin_id')
            )
            
            saved_exchange = self.exchange_repo.create_if_not_exists(exchange)
            return saved_exchange
            
        except Exception:
            return None

    def _get_description(self, description_dict: Dict) -> Optional[str]:
        if not description_dict:
            return None
        return description_dict.get('en', '')

    def _get_first_link(self, links_list: List) -> Optional[str]:
        if not links_list or not isinstance(links_list, list):
            return None
        filtered_links = [link for link in links_list if link and link.strip()]
        return filtered_links[0] if filtered_links else None

    def _format_twitter_link(self, username: str) -> Optional[str]:
        if not username or not username.strip():
            return None
        return f"https://twitter.com/{username.strip()}"

    def _format_twitter_handle(self, handle: str) -> Optional[str]:
        if not handle or not handle.strip():
            return None
        return f"https://twitter.com/{handle.strip()}"

    def _format_facebook_link(self, username: str) -> Optional[str]:
        if not username or not username.strip():
            return None
        return f"https://facebook.com/{username.strip()}"

    def _format_instagram_link(self, username: str) -> Optional[str]:
        if not username or not username.strip():
            return None
        return f"https://instagram.com/{username.strip()}"

    def _safe_str(self, value) -> Optional[str]:
        if value is None:
            return None
        return str(value)

    def _name_to_id(self, name: str) -> str:
        return name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('.', '')
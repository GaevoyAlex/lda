import requests
import time
import asyncio
import aiohttp
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any, List

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
    
    REQUEST_TIMEOUT = 10
    BATCH_SIZE = 50
    EXCHANGE_BATCH_SIZE = 20

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
        
        self._init_repositories()

    def _init_repositories(self):
        self.token_repo = TokensRepository()
        self.platform_repo = PlatformRepository()
        self.exchange_repo = ExchangeRepository()
        self.token_stats_repo = TokenStatsRepository()
        self.exchanges_stats_repo = ExchangesStatsRepository()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params, 
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None

    async def _make_async_request(self, session: aiohttp.ClientSession, 
                                endpoint: str, params: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}/{endpoint}"
        try:
            timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
            async with session.get(url, headers=self.headers, params=params, timeout=timeout) as response:
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

        stats_batch = self._process_market_coins(market_coins)
        updated_count, failed_count = self._save_token_stats_batch(stats_batch)

        total_time = time.time() - start_time
        print(f"Completed: {updated_count} saved, {failed_count} failed in {total_time:.2f}s")

    def _process_market_coins(self, market_coins: List[Dict]) -> List[TokenStats]:
        stats_batch = []
        for market_coin in market_coins:
            try:
                stats = self._create_token_stats_from_market(market_coin)
                if stats:
                    stats_batch.append(stats)
            except Exception:
                continue
        return stats_batch

    def _save_token_stats_batch(self, stats_batch: List[TokenStats]) -> tuple:
        updated_count = 0
        failed_count = 0
        
        for stats in stats_batch:
            try:
                self.token_stats_repo.create_or_update(stats)
                updated_count += 1
            except Exception:
                failed_count += 1
                
        return updated_count, failed_count

    def update_exchanges_stats_every_10_seconds(self, limit: int = 100) -> None:
        print(f"Updating ExchangesStats from list data (limit: {limit})...")
        start_time = time.time()
        
        exchanges_list = self.get_exchanges_list(limit)
        if not exchanges_list:
            print("No exchanges data received")
            return
        
        print(f"Received {len(exchanges_list)} exchanges in {time.time() - start_time:.2f}s")
        
        updated_count, failed_count = self._process_exchanges_list(exchanges_list)
        
        total_time = time.time() - start_time
        print(f"Completed: {updated_count} updated, {failed_count} failed in {total_time:.2f}s")

    def _process_exchanges_list(self, exchanges_list: List[Dict]) -> tuple:
        updated_count = 0
        failed_count = 0
        
        for exchange_data in exchanges_list:
            try:
                self._save_exchange_stats_from_list(exchange_data)
                updated_count += 1
            except Exception:
                failed_count += 1
                
        return updated_count, failed_count

    async def collect_tokens_detailed_info_daily_async(self, limit: int = 500) -> None:
        print(f"Collecting detailed info for tokens (daily task, limit: {limit})...")
        start_time = time.time()
        
        coingecko_ids = self._get_token_coingecko_ids(limit)
        if not coingecko_ids:
            print("No tokens found in TokenStats")
            return
        
        print(f"Found {len(coingecko_ids)} unique tokens to process")
        
        saved_count, failed_count = await self._process_tokens_detailed_async(coingecko_ids, start_time)

        total_time = time.time() - start_time
        print(f"Completed in {total_time:.2f}s: {saved_count} saved, {failed_count} failed")

    def _get_token_coingecko_ids(self, limit: int) -> List[str]:
        all_token_stats = self.token_stats_repo.get_all()
        coingecko_ids = list(set([
            ts.get('coingecko_id') for ts in all_token_stats 
            if ts.get('coingecko_id')
        ]))
        return coingecko_ids[:limit]

    async def _process_tokens_detailed_async(self, coingecko_ids: List[str], start_time: float) -> tuple:
        saved_count = 0
        failed_count = 0
        total_to_process = len(coingecko_ids)
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(coingecko_ids), self.BATCH_SIZE):
                batch = coingecko_ids[i:i + self.BATCH_SIZE]
                tasks = [self._save_token_detailed_info_async(session, coin_id) for coin_id in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                batch_saved, batch_failed = self._count_results(results)
                saved_count += batch_saved
                failed_count += batch_failed
                
                self._log_progress(i + self.BATCH_SIZE, len(coingecko_ids), total_to_process, start_time)
                await asyncio.sleep(0.5)

        return saved_count, failed_count

    def _count_results(self, results: List) -> tuple:
        saved_count = 0
        failed_count = 0
        
        for result in results:
            if result and not isinstance(result, Exception):
                saved_count += 1
            else:
                failed_count += 1
                
        return saved_count, failed_count

    def _log_progress(self, processed: int, total_ids: int, total_to_process: int, start_time: float):
        if processed % 100 == 0 or processed >= total_ids:
            elapsed = time.time() - start_time
            rate = min(processed, total_ids) / elapsed if elapsed > 0 else 0
            eta = (total_to_process - min(processed, total_ids)) / rate if rate > 0 else 0
            print(f"Progress: {min(processed, total_ids)}/{total_to_process} ({rate:.1f}/s, ETA: {eta:.0f}s)")

    async def collect_exchanges_detailed_info_daily_async(self, limit: int = 100) -> None:
        print(f"Collecting detailed info for exchanges (daily task, limit: {limit})...")
        start_time = time.time()
        
        exchange_names = self._get_exchange_names(limit)
        if not exchange_names:
            print("No exchanges found in ExchangeStats")
            return
        
        print(f"Found {len(exchange_names)} exchanges to process")
        
        saved_count, failed_count = await self._process_exchanges_detailed_async(exchange_names)

        total_time = time.time() - start_time
        print(f"Successfully saved detailed info for {saved_count} exchanges in {total_time:.2f}s, {failed_count} failed")

    def _get_exchange_names(self, limit: int) -> List[str]:
        all_exchange_stats = self.exchanges_stats_repo.get_all()
        exchange_names = list(set([
            es.get('name') for es in all_exchange_stats 
            if es.get('name')
        ]))
        return exchange_names[:limit]

    async def _process_exchanges_detailed_async(self, exchange_names: List[str]) -> tuple:
        saved_count = 0
        failed_count = 0
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(exchange_names), self.EXCHANGE_BATCH_SIZE):
                batch = exchange_names[i:i + self.EXCHANGE_BATCH_SIZE]
                tasks = []
                
                for exchange_name in batch:
                    exchange_id = self._name_to_id(exchange_name)
                    tasks.append(self._save_exchange_detailed_info_async(session, exchange_id))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                batch_saved, batch_failed = self._count_results(results)
                saved_count += batch_saved
                failed_count += batch_failed
                
                processed = min(i + self.EXCHANGE_BATCH_SIZE, len(exchange_names))
                print(f"Processed {processed}/{len(exchange_names)} exchanges")
                
                await asyncio.sleep(0.5)
                
        return saved_count, failed_count

    def collect_tokens_detailed_info_daily(self, limit: int = 500) -> None:
        asyncio.run(self.collect_tokens_detailed_info_daily_async(limit))

    def collect_exchanges_detailed_info_daily(self, limit: int = 100) -> None:
        asyncio.run(self.collect_exchanges_detailed_info_daily_async(limit))

    def _create_token_stats_from_market(self, market_coin: Dict) -> Optional[TokenStats]:
        try:
            symbol = market_coin.get('symbol', '').upper()
            coingecko_id = market_coin.get('id')

            if not symbol or not coingecko_id:
                return None

            market_cap_usd = market_coin.get('market_cap')
            volume_24h_usd = market_coin.get('total_volume')
            liquidity_score = self._calculate_liquidity_score(market_cap_usd, volume_24h_usd)
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

    def _calculate_liquidity_score(self, market_cap_usd: float, volume_24h_usd: float) -> Optional[str]:
        if market_cap_usd and volume_24h_usd and market_cap_usd > 0:
            return str(round((volume_24h_usd / market_cap_usd) * 100, 4))
        return None

    def _calculate_tvl_from_market(self, market_coin: Dict) -> Optional[str]:
        try:
            market_cap = market_coin.get('market_cap')
            total_volume = market_coin.get('total_volume')
            
            if not market_cap or not total_volume:
                return None
                
            velocity = total_volume / market_cap if market_cap > 0 else 0
            tvl_factor = max(0.1, min(2.0, 1 / (1 + velocity * 10)))
            estimated_tvl = market_cap * tvl_factor * 0.3
            return str(round(estimated_tvl, 2))
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
            token = self._create_token_from_details(coin_details)
            saved_token = self.token_repo.create_if_not_exists(token)
            self._save_token_platforms(coin_details, saved_token['id'])
            return saved_token
        except Exception:
            return None

    def _create_token_from_details(self, coin_details: Dict) -> Token:
        links = coin_details.get('links', {})
        
        return Token(
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

    def _save_token_platforms(self, coin_details: Dict, token_id: str):
        platforms = coin_details.get('platforms', {})
        for platform_name, address in platforms.items():
            if address and address.strip():
                platform = Platform(
                    token_id=token_id,
                    name=platform_name,
                    token_address=address
                )
                self.platform_repo.create_if_not_exists(platform)

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
            
            return self.exchange_repo.create_if_not_exists(exchange)
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
        return self._format_social_link(username, "https://twitter.com/")

    def _format_twitter_handle(self, handle: str) -> Optional[str]:
        return self._format_social_link(handle, "https://twitter.com/")

    def _format_facebook_link(self, username: str) -> Optional[str]:
        return self._format_social_link(username, "https://facebook.com/")

    def _format_instagram_link(self, username: str) -> Optional[str]:
        return self._format_social_link(username, "https://instagram.com/")

    def _format_social_link(self, username: str, base_url: str) -> Optional[str]:
        if not username or not username.strip():
            return None
        return f"{base_url}{username.strip()}"

    def _safe_str(self, value) -> Optional[str]:
        return str(value) if value is not None else None

    def _name_to_id(self, name: str) -> str:
        return name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('.', '')
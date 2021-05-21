import os
import json


class Asset:
    def __init__(self, words):
        self.asset_class = words[0]
        self.product_type_ind = words[1]
        self.asset_desc = words[2]
        self.symbol = words[3]
        self.quantity = words[4]
        self.average_cost = words[5]
        self.total_cost = words[7]
        self.denom = words[8]
        self.current_price = words[9]
        self.market_value_cad = words[11]
        self.unrealized_gain_loss = words[13]
        self.unrealized_gain_loss_percent = words[15]
        self.portfolio_percent = words[16]
        self.annualized_income = words[22]
        self.annualized_yield = words[24]
        self.annual_dividend = words[25]
        self.dividend_freq = words[27]
        self.ex_dividend_date = words[28]

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def get_tuple(self, rpt_date):
        return (
            rpt_date,
            self.asset_class,
            self.product_type_ind,
            self.asset_desc,
            self.symbol,
            self.quantity,
            self.average_cost,
            self.total_cost,
            self.denom,
            self.current_price,
            self.market_value_cad,
            self.unrealized_gain_loss,
            self.unrealized_gain_loss_percent,
            self.portfolio_percent,
            self.annualized_income,
            self.annualized_yield,
            self.annual_dividend,
            self.dividend_freq,
            self.ex_dividend_date
        )


class CashBalance:
    def __init__(self, words):
        self.market_value = words[11]
        self.cash = words[4]
        self.current_price = words[9]
        self.portfolio_percent_CAD = words[16].strip('\n')
        if words[2].startswith("Canadian"):
            self.denom = "CAD"
        elif words[2].startswith("U.S."):
            self.denom = "USD"

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def get_tuple(self, rpt_date):
        return (
            rpt_date,
            self.market_value,
            self.cash,
            self.current_price,
            self.portfolio_percent_CAD,
            self.denom
        )


class AssetItem:
    CATEGORY_DEF = {
        "VTI:US": {"name": "USTotalStockMarket", "percent": 15.0},
        "VB:US": {"name": "USSmallCap", "percent": 15.0},
        "VNQ:US": {"name": "RealEstate", "percent": 5.0},
        "VWO:US": {"name": "EmergingMarkets", "percent": 10.0},
        "VPL:US": {"name": "PacificStocks", "percent": 10.0},
        "VGK:US": {"name": "EuropeanStocks", "percent": 10.0},
        "BND:US": {"name": "USTotalBondMarket", "percent": 10.0},
        "GDX:US": {"name": "PrecousMetals", "percent": 5.0},
        "HYG:US": {"name": "HighYieldCorpBonds", "percent": 10.0},
        "TIP:US": {"name": "TreasuryInflationProtectedSecurities", "percent": 10.0},
        "TSLA:US": {"name": "Tesla", "percent": 0.0},
        "VV:US": {"name": "LargeCapStock", "percent": 0.0},
        "VIG:US": {"name": "DividendAppreciation", "percent": 0.0},
        "XIC": {"name": "TSX Capped Composite Index ETF", "percent": 0.0},
    }

    def __init__(self, symbol):
        if symbol not in AssetItem.CATEGORY_DEF:
            raise ValueError(f"Symbol {symbol} is not configured")
        self.symbol = symbol
        self.name = AssetItem.CATEGORY_DEF[symbol]["name"]
        self.percent = AssetItem.CATEGORY_DEF[symbol]["percent"]
        self.current_percent = 0.0
        self.market_value_cad = 0.0
        self.target_market_value_cad = 0.0
        self.price_cad = 0.0
        self.order_units = 0
        self.denom = "USD"


class Portfolio:
    Asset_Class = ('Fixed income', 'Equities')
    Product_Type_Ind = ('Other Securities', 'Equity Funds',
                        'Materials', 'Real Estate')

    def __init__(self, csv_filename):
        self.report_file = csv_filename.split(os.sep)[-1]
        self.instream = open(csv_filename, 'r')
        self.cash_balances: CashBalance = []
        self.asset_items: AssetItem = dict()
        self.assets: Asset = []
        self.load(csv_filename)
        self.gf_total = 0.0
        self.cash_total = 0.0
        self.exchange_rate = 0.0
        self.proc_asset_items()

    def proc_asset_items(self):
        for cashasset in self.cash_balances:
            self.cash_total += float(cashasset.market_value)
            if cashasset.denom == "USD":
                self.exchange_rate = float(cashasset.current_price)
            self.gf_total = self.cash_total
        for asset in self.assets:
            if asset.symbol in AssetItem.CATEGORY_DEF:
                if asset.symbol in self.asset_items.keys():
                    asset_item = self.asset_items[asset.symbol]
                else:
                    asset_item = AssetItem(asset.symbol)
                asset_item.market_value_cad += float(asset.market_value_cad)
                asset_item.denom = asset.denom
                asset_item.price_cad = float(asset.current_price) * self.exchange_rate
                if asset_item.percent > 0:
                    self.gf_total += float(asset.market_value_cad)
                self.asset_items[asset.symbol] = asset_item
            else:
                raise ValueError(f"proc_asset_items symbol {asset.symbol} not configured")
        for asset_item in self.asset_items.values():
            if asset_item.percent == 0:
                continue
            asset_item.target_market_value_cad = (asset_item.percent / 100) * self.gf_total
            asset_item.current_percent = (asset_item.market_value_cad / self.gf_total) * 100
            asset_item.order_units = (asset_item.target_market_value_cad - asset_item.market_value_cad) / asset_item.price_cad 

    def load(self, csv_filename):
        words = read_line(self.instream)
        if len(words) < 2 or not str(words[0]).startswith('Account:'):
            raise Exception("Corrupt or missing account section")
        self.account = words[1].strip('\n')

        words = read_line(self.instream)
        if len(words) < 2 or not str(words[0]).startswith('as of date:'):
            raise Exception("Corrupt or missing date section")
        self.report_date = words[1].strip('\n')

        skip(self.instream, 2)

        words = read_line(self.instream)

        if len(words) < 6 or not words[0].startswith('Total'):
            raise Exception("Corrupt or missing cash section")
        self.cash_total = words[1]
        self.denom = words[2]
        self.securities_total = words[3]
        self.acct_balance = words[5]

        skip(self.instream, 3)
        while True:
            words = read_line(self.instream)
            if len(words) > 1 and str(words[0]).startswith('Cash balances'):  # todo
                self.cash_balances.append(CashBalance(words))
            # todo
            elif len(words) > 1 and str(words[0]).startswith('Total cash balances'):
                self.market_value_cash = words[11]
                self.total_cash_portfolio_percent = words[16].strip('\n')
                break

        skip(self.instream, 3)
        while True:
            words = read_line(self.instream)
            # process asset classes
            if len(words) > 1 and self.Asset_Class.__contains__(words[0]):
                self.assets.append(Asset(words))
            elif len(words) > 1 and words[0].startswith('Total portfolio value'):
                self.total_portfolio_market_value = words[11]
                self.total_unrealized_gain_loss = words[13]
                self.total_unrealized_gain_loss_percent = words[15]
                break

    def get_tuple(self):
        '''
        Returns three tuples, first single field report values, second a list of cash balances
        and third is a list of assets
        '''
        pfolio = (self.report_date,
                  self.report_file,
                  self.account,
                  self.cash_total,
                  self.denom,
                  self.securities_total,
                  self.acct_balance,
                  self.market_value_cash,
                  self.total_cash_portfolio_percent,
                  self.total_portfolio_market_value,
                  self.total_unrealized_gain_loss,
                  self.total_unrealized_gain_loss_percent,
                  )
        cbs = [cb.get_tuple(self.report_date) for cb in self.cash_balances]
        assets = [acct.get_tuple(self.report_date) for acct in self.assets]
        return (pfolio, cbs, assets)

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)


def read_line(instream):
    line = instream.readline()
    return line.split(',')


def skip(instream, linestoskip):
    for i in range(linestoskip):
        instream.readline()

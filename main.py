import sys,os,json,jsonpickle
from template.csvbase import Portfolio,AssetItem


def process_csv():
    csv_in_report = sys.argv[1]
    portfolios = []
    if os.path.isdir(csv_in_report):
        csv_in_report_folder = csv_in_report
        print('{ "Assets":[')
        first = True
        for filename in os.listdir(csv_in_report_folder):
            if not first:
                print(',')
                first = False
            portfolios.append(process_file(os.path.join(csv_in_report_folder, filename)))
        print(']')
    else:
        portfolios.append(process_file(csv_in_report))
    return portfolios

def process_file(filename: str):
    if filename.endswith(".csv"):
        report = Portfolio(filename)
        #print(jsonpickle.encode(report, unpicklable=False, indent=4))
        return report

def print_cash_balances(reports: list):
    for _portfolio in reports:
        (portfolio_tuple, cash_balances_tuple, assets_tuple) = _portfolio.get_tuple()
        print(cash_balances_tuple)
        print(portfolio_tuple)
        print(assets_tuple)


if __name__ == '__main__':
    portfolios: list = process_csv()
    for portfolio in portfolios:
        asset_rpt = portfolio.asset_items
        print(jsonpickle.encode(asset_rpt, unpicklable=False, indent=4))
        total_order_cad = 0.0
        for asset in asset_rpt.values():
            if(asset.order_units > 0):
                total_order_cad += asset.order_units * asset.price_cad
        print(f"Total value of order: {total_order_cad}")



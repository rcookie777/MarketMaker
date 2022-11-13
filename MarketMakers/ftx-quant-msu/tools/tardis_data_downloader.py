# requires Python >=3.6
# pip install tardis-dev

from tardis_dev import datasets, get_exchange_details
import logging
from argparse import ArgumentParser
from tqdm import tqdm


def download_and_save_data(exchange, api_key, output_folder):
    # optionally enable debug logs
    # logging.basicConfig(level=logging.DEBUG)

    exchange_details = get_exchange_details(exchange)
    num_symbols = len(exchange_details["datasets"]["symbols"])

    # iterate over and download all data for every symbol
    with tqdm(total=num_symbols) as progress_bar:
        for symbol in exchange_details["datasets"]["symbols"]:
            # alternatively specify datatypes explicitly ['trades', 'incremental_book_L2', 'quotes'] etc
            # see available options
            # https://docs.tardis.dev/downloadable-csv-files#data-types
            data_types = symbol["dataTypes"]
            symbol_id = symbol["id"]
            from_date = symbol["availableSince"]
            to_date = symbol["availableTo"]
            progress_bar.set_description(f"{exchange}, {symbol_id}"
                                         f" from {from_date} to {to_date}")

            # skip groupped symbols
            # if symbol_id in ['PERPETUALS', 'SPOT', 'FUTURES']:
            # only spot in us
            if symbol_id in ['SPOT']:
                continue

            # each CSV dataset format is documented at https://docs.tardis.dev/downloadable-csv-files#data-types
            # see
            # https://docs.tardis.dev/downloadable-csv-files#download-via-client-libraries
            # for full options docs
            datasets.download(
                exchange=exchange,
                data_types=data_types,
                from_date=from_date,
                to_date=to_date,
                symbols=[symbol_id],
                # TODO set your API key here
                api_key=api_key,
                # path where CSV data will be downloaded into
                download_dir=output_folder,
            )
            progress_bar.update()


if __name__ == "__main__":

    arg_parser = ArgumentParser()
    arg_parser.add_argument('--api_key', type=str, required=True,
                            help="Exchange api key")
    arg_parser.add_argument('--output_folder', type=str, default="./data",
                            help="Location to save output")
    arg_parser.add_argument('--exchange', type=str, required=True,
                            help="ftx-us")
    args = arg_parser.parse_args()

    download_and_save_data(args.exchange, args.api_key, args.output_folder)

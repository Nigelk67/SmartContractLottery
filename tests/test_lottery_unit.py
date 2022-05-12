from asyncio import exceptions
from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3
import pytest
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)

# NEED TO TEST ALL LINES OF CODE!


def test_get_entrance_fee():

    # THIS IS A SANITY CHECK TEST ONLY!
    # Expected value of Eth for $50 based on Ether price in CoinDesk = 0.0176
    # assert lottery.getEntranceFee() > Web3.toWei(0.017, "ether")
    # assert lottery.getEntranceFee() < Web3.toWei(0.019, "ether")
    # account = accounts[0]
    # lottery = Lottery.deploy(
    #   config["networks"][network.show_active()]["eth_usd_price_feed"],
    #  {"from": account},
    # )

    # ******---MORE ROBUST TEST---****:-
    # ONLY run on local deve network:-
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip

    # Arrange:
    lottery = deploy_lottery()
    # Act:
    # 2,000 eth / usd (see helpful_scripts deploy_mocks -> INITIAL_VALUE)
    # USD entrance fee is 50
    # 2000/1 == 50/x == 0.025
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    entrance_fee = lottery.getEntranceFee()
    # Assert:
    expected_entrance_fee == entrance_fee


def test_cant_enter_unless_started():
    # ONLY run on local deve network:-
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip
    lottery = deploy_lottery()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    # ONLY run on local deve network:-
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    assert lottery.players(0) == account


def test_can_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    # 2 represents the position of CALCULATING_WINNER in the LotteryState enum
    assert lottery.lottery_state() == 2


def test_can_pick_winner_correcly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomnness"]["requestId"]
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )
    # 777 % 3 = 0 therefore the winner is the account at index 0.
    starting_balance_of_account = account.balance()
    balance_of_lottery = lottery.balance()
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + balance_of_lottery

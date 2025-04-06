# bot/main.py
import os
import logging
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    FSInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import pandas as pd
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)


# States
class ExpenseStates(StatesGroup):
    MENU = State()
    ADD_NAME = State()
    ADD_DATE = State()
    ADD_AMOUNT = State()
    REPORT_START = State()
    REPORT_END = State()
    DELETE_ID = State()
    EDIT_ID = State()
    EDIT_NAME = State()
    EDIT_AMOUNT = State()


# Helper functions
async def fetch_expenses(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
) -> Optional[List[Dict[str, Any]]]:
    """Fetch expenses from API"""
    url = f"{API_BASE_URL}/expenses/"
    params = {}

    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                logger.error(f"API returned status {response.status}")
                return None
    except Exception as e:
        logger.error(f"Error fetching expenses: {e}")
        return None


async def create_expense(name: str, date_str: str, amount: float) -> bool:
    """Create new expense via API"""
    try:
        expense_date = datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        return False

    url = f"{API_BASE_URL}/expenses/"
    data = {
        "name": name,
        "date": expense_date.isoformat(),
        "amount_uah": float(amount)
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Error creating expense: {e}")
        return False


async def delete_expense(expense_id: int) -> bool:
    """Delete expense via API"""
    url = f"{API_BASE_URL}/expenses/{expense_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Error deleting expense: {e}")
        return False


async def update_expense(
        expense_id: int,
        name: Optional[str] = None,
        amount: Optional[float] = None
) -> bool:
    """Update expense via API"""
    url = f"{API_BASE_URL}/expenses/{expense_id}"
    data = {}

    if name:
        data["name"] = name
    if amount:
        data["amount_uah"] = float(amount)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=data) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Error updating expense: {e}")
        return False


def create_excel_report(expenses: List[Dict[str, Any]]) -> str:
    """Generate Excel report from expenses"""
    if not expenses:
        raise ValueError("No expenses to generate report")

    df = pd.DataFrame(expenses)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%d.%m.%Y')
    df = df[['id', 'name', 'date', 'amount_uah', 'amount_usd']]
    df.columns = ['ID', 'Name', 'Date', 'Amount (UAH)', 'Amount (USD)']

    filename = "expenses_report.xlsx"
    df.to_excel(filename, index=False)
    return filename


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Create main menu keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💵 Add Expense")],
            [KeyboardButton(text="📈 Get Report")],
            [KeyboardButton(text="🗑 Delete Expense")],
            [KeyboardButton(text="✏️ Edit Expense")]
        ],
        resize_keyboard=True
    )


# Handlers
@router.message(Command("start", "menu"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start and /menu commands"""
    await state.clear()
    await state.set_state(ExpenseStates.MENU)
    await message.answer(
        "Welcome to Expense Tracker Bot! Choose an action:",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "💵 Add Expense", ExpenseStates.MENU)
async def add_expense_name(message: Message, state: FSMContext):
    """Start adding new expense - ask for name"""
    await state.set_state(ExpenseStates.ADD_NAME)
    await message.answer(
        "Enter expense name:",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(ExpenseStates.ADD_NAME)
async def add_expense_date(message: Message, state: FSMContext):
    """Get expense name and ask for date"""
    if len(message.text) > 100:
        await message.answer("Name is too long (max 100 characters). Please try again:")
        return

    await state.update_data(name=message.text)
    await state.set_state(ExpenseStates.ADD_DATE)
    await message.answer("Enter date in DD.MM.YYYY format:")


@router.message(ExpenseStates.ADD_DATE)
async def add_expense_amount(message: Message, state: FSMContext):
    """Get expense date and ask for amount"""
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.answer("Invalid date format. Please use DD.MM.YYYY:")
        return

    await state.update_data(date=message.text)
    await state.set_state(ExpenseStates.ADD_AMOUNT)
    await message.answer("Enter amount in UAH:")


@router.message(ExpenseStates.ADD_AMOUNT)
async def process_add_expense(message: Message, state: FSMContext):
    """Get expense amount and save to API"""
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        await message.answer("Please enter a valid positive number:")
        return

    data = await state.get_data()
    success = await create_expense(data['name'], data['date'], amount)

    if success:
        await message.answer("✅ Expense added successfully!")
    else:
        await message.answer("❌ Failed to add expense. Please try again.")

    await state.set_state(ExpenseStates.MENU)
    await cmd_start(message, state)


@router.message(F.text == "📈 Get Report", ExpenseStates.MENU)
async def report_start_date(message: Message, state: FSMContext):
    """Start report generation - ask for start date"""
    await state.set_state(ExpenseStates.REPORT_START)
    await message.answer(
        "Enter start date (DD.MM.YYYY):",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(ExpenseStates.REPORT_START)
async def report_end_date(message: Message, state: FSMContext):
    """Get start date and ask for end date"""
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.answer("Invalid date format. Please use DD.MM.YYYY:")
        return

    await state.update_data(report_start=message.text)
    await state.set_state(ExpenseStates.REPORT_END)
    await message.answer("Enter end date (DD.MM.YYYY):")


@router.message(ExpenseStates.REPORT_END)
async def process_report(message: Message, state: FSMContext):
    """Get end date, generate and send report"""
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.answer("Invalid date format. Please use DD.MM.YYYY:")
        return

    data = await state.get_data()
    try:
        start_date = datetime.strptime(data['report_start'], "%d.%m.%Y").date()
        end_date = datetime.strptime(message.text, "%d.%m.%Y").date()

        if start_date > end_date:
            await message.answer("Start date must be before end date. Please try again.")
            return

        expenses = await fetch_expenses(start_date, end_date)

        if not expenses:
            await message.answer("No expenses found for this period.")
            await state.set_state(ExpenseStates.MENU)
            await cmd_start(message, state)
            return

        filename = create_excel_report(expenses)

        total_uah = sum(expense['amount_uah'] for expense in expenses)
        total_usd = sum(expense['amount_usd'] for expense in expenses)

        with open(filename, 'rb') as file:
            await message.answer_document(
                document=FSInputFile(filename),
                caption=f"📊 Expense report from {start_date.strftime('%d.%m.%Y')} to {end_date.strftime('%d.%m.%Y')}\n"
                        f"💵 Total: {total_uah:.2f} UAH ({total_usd:.2f} USD)"
            )
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await message.answer("❌ Error generating report. Please try again.")
    finally:
        await state.set_state(ExpenseStates.MENU)
        await cmd_start(message, state)


@router.message(F.text == "🗑 Delete Expense", ExpenseStates.MENU)
async def delete_expense_start(message: Message, state: FSMContext):
    """Start delete process - fetch and show all expenses"""
    expenses = await fetch_expenses()

    if not expenses:
        await message.answer("No expenses found to delete.")
        return

    try:
        filename = create_excel_report(expenses)

        with open(filename, 'rb') as file:
            await message.answer_document(
                document=FSInputFile(filename),
                caption="Select ID of expense to delete:",
                reply_markup=ReplyKeyboardRemove()
            )

        await state.set_state(ExpenseStates.DELETE_ID)
    except Exception as e:
        logger.error(f"Error preparing delete: {e}")
        await message.answer("❌ Error preparing expenses list. Please try again.")


@router.message(ExpenseStates.DELETE_ID)
async def process_delete_expense(message: Message, state: FSMContext):
    """Process expense deletion by ID"""
    try:
        expense_id = int(message.text)
        if expense_id <= 0:
            raise ValueError("ID must be positive")
    except ValueError:
        await message.answer("Please enter a valid positive ID number:")
        return

    success = await delete_expense(expense_id)

    if success:
        await message.answer("✅ Expense deleted successfully!")
    else:
        await message.answer("❌ Failed to delete expense. Please check ID and try again.")

    await state.set_state(ExpenseStates.MENU)
    await cmd_start(message, state)


@router.message(F.text == "✏️ Edit Expense", ExpenseStates.MENU)
async def edit_expense_start(message: Message, state: FSMContext):
    """Start edit process - fetch and show all expenses"""
    expenses = await fetch_expenses()

    if not expenses:
        await message.answer("No expenses found to edit.")
        return

    try:
        filename = create_excel_report(expenses)

        with open(filename, 'rb') as file:
            await message.answer_document(
                document=FSInputFile(filename),
                caption="Select ID of expense to edit:",
                reply_markup=ReplyKeyboardRemove()
            )

        await state.set_state(ExpenseStates.EDIT_ID)
    except Exception as e:
        logger.error(f"Error preparing edit: {e}")
        await message.answer("❌ Error preparing expenses list. Please try again.")


@router.message(ExpenseStates.EDIT_ID)
async def edit_expense_select(message: Message, state: FSMContext):
    """Select expense to edit by ID"""
    try:
        expense_id = int(message.text)
        if expense_id <= 0:
            raise ValueError("ID must be positive")
    except ValueError:
        await message.answer("Please enter a valid positive ID number:")
        return

    expenses = await fetch_expenses()
    expense = next((e for e in expenses if e['id'] == expense_id), None)

    if not expense:
        await message.answer("Expense with this ID not found. Please try again.")
        return

    await state.update_data(edit_id=expense_id)
    await message.answer(
        f"Current expense info:\n"
        f"📌 Name: {expense['name']}\n"
        f"📅 Date: {expense['date']}\n"
        f"💵 Amount: {expense['amount_uah']} UAH\n\n"
        f"Enter new name (or send '-' to keep current):"
    )
    await state.set_state(ExpenseStates.EDIT_NAME)


@router.message(ExpenseStates.EDIT_NAME)
async def edit_expense_amount(message: Message, state: FSMContext):
    """Get new name and ask for new amount"""
    if message.text.strip() != "-":
        if len(message.text) > 100:
            await message.answer("Name is too long (max 100 characters). Please try again:")
            return
        await state.update_data(edit_name=message.text)
    else:
        await state.update_data(edit_name=None)

    await state.set_state(ExpenseStates.EDIT_AMOUNT)
    await message.answer("Enter new amount in UAH (or send '-' to keep current):")


@router.message(ExpenseStates.EDIT_AMOUNT)
async def process_edit_expense(message: Message, state: FSMContext):
    """Process expense editing"""
    data = await state.get_data()
    expense_id = data['edit_id']

    new_name = data.get('edit_name')
    new_amount = None

    if message.text.strip() != "-":
        try:
            new_amount = float(message.text)
            if new_amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            await message.answer("Please enter a valid positive number:")
            return

    success = await update_expense(expense_id, new_name, new_amount)

    if success:
        await message.answer("✅ Expense updated successfully!")
    else:
        await message.answer("❌ Failed to update expense. Please try again.")

    await state.set_state(ExpenseStates.MENU)
    await cmd_start(message, state)


@router.message(ExpenseStates.MENU)
async def handle_unknown(message: Message):
    """Handle unknown commands in MENU state"""
    await message.answer(
        "Please choose an option from the menu below:",
        reply_markup=get_main_menu_keyboard()
    )


async def main():
    """Start the bot"""
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
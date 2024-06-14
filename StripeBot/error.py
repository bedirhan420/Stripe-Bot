from telegram import Update
from telegram.ext import ContextTypes


#ERROR
async def error(update: Update,context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')
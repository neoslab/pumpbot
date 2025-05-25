# Import packages
from app import PumpBotUI
from bot import PumpBotManager


# Function 'main'
def main():
    """ Function description """
    # Start User Interface
    app = PumpBotUI()
    app.run()

    # Start Bot Handler
    #bot = PumpBotManager()
    #bot.run()


# Main callback
if __name__ == '__main__':
    """ Callback description """
    main()
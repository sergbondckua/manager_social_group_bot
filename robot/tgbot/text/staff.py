from aiogram.utils.markdown import text, hbold, hitalic, hcode

post_template = text(
    hbold("📬 {title}\n"),
    "🔄 " + hbold("Періодичність: ") + hitalic("{periodicity}"),
    "⏰ " + hbold("Час розсилки: ") + hcode("{scheduled_time}\n"),
    "⌨ " + hbold("Прев'ю: ") + hitalic("/chrono_preview_{post_id}"),
    "=====================\n",
    sep="\n"
)

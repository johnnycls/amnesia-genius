style default:
    font "fonts/NotoSansCJKsc-Regular.otf"

style app_text:
    color "#e8edf2"
    size 22

style app_small:
    color "#aeb8c2"
    size 16

style app_button:
    background "#263746"
    hover_background "#36546a"
    padding (14, 8)

style app_button_text:
    color "#e8edf2"
    hover_color "#ffffff"
    size 20

screen agent_shell():
    tag agent_shell
    add Solid("#101820")

    frame:
        style_prefix "app"
        xalign 0.5
        yalign 0.5
        xmaximum 1400
        ymaximum 850
        xfill True
        yfill True
        padding (28, 24)

        vbox:
            spacing 16

            hbox:
                spacing 12
                text _("Amnesia Agent") size 34 bold True
                null width 30
                textbutton _("Chat") action SetVariable("active_tab", "chat")
                textbutton _("Settings") action SetVariable("active_tab", "settings")
                textbutton _("Workspace") action [SetVariable("active_tab", "workspace"), Function(controller.load_workspace_async)]
                textbutton _("Language") action SetVariable("active_tab", "settings")

            text controller.status style "app_small"

            if active_tab == "chat":
                use chat_panel
            elif active_tab == "settings":
                use settings_panel
            else:
                use workspace_panel

screen chat_panel():
    vbox:
        spacing 12
        viewport:
            ysize 570
            mousewheel True
            draggable True
            scrollbars "vertical"
            vbox:
                spacing 12
                for message in controller.messages:
                    if message.get("role") == "user":
                        text "[_('You:')] [message.get('text', '')]" style "app_text"
                    elif message.get("role") == "assistant":
                        text "[_('Agent:')] [message.get('text', '')]" style "app_text"
                        if message.get("choices", []):
                            hbox:
                                spacing 10
                                for choice in message.get("choices", []):
                                    textbutton choice action Function(controller.choose, choice)
                    elif message.get("role") == "error":
                        text "[_('Error:')] [message.get('text', '')]" color "#ff8d8d" style "app_text"
                    elif message.get("role") == "tool_call":
                        text _("Tool call") style "app_small"
                    elif message.get("role") == "tool_result":
                        text "[_('Tool result:')] [message.get('data', {}).get('content', '')]" style "app_small"
                if controller.streaming_text:
                    text "[_('Agent:')] [controller.streaming_text]" style "app_text"

        hbox:
            spacing 10
            input:
                value VariableInputValue("input_text")
                xfill True
                length 400
                pixel_width 900
                style "app_text"
            textbutton _("Send") sensitive (not controller.busy and controller.started) action Function(controller.send, input_text)
            textbutton _("Cancel") sensitive controller.busy action Function(controller.cancel)

screen settings_panel():
    viewport:
        mousewheel True
        draggable True
        scrollbars "vertical"
        vbox:
            spacing 10
            text _("Interface language") size 28 bold True
            text "[_('Current language:')] [language_name()]" style "app_small"
            hbox:
                spacing 8
                textbutton "English" action Function(set_ui_language, "english")
                textbutton "简体中文" action Function(set_ui_language, "schinese")
                textbutton "繁體中文" action Function(set_ui_language, "tchinese")
                textbutton "日本語" action Function(set_ui_language, "japanese")
                textbutton "한국어" action Function(set_ui_language, "korean")

            text _("Provider") size 28 bold True
            text _("Model") style "app_small"
            input value VariableInputValue("settings_model") xfill True
            text _("API key (leave blank to keep the current key)") style "app_small"
            input value VariableInputValue("settings_api_key") xfill True mask "*"
            text _("Base URL") style "app_small"
            input value VariableInputValue("settings_base_url") xfill True
            text _("Provider params (JSON object)") style "app_small"
            input value VariableInputValue("settings_provider_params") xfill True multiline True ymaximum 100

            text _("Execution limits") size 28 bold True
            text _("Command timeout seconds") style "app_small"
            input value VariableInputValue("settings_timeout") xfill True
            text _("Maximum command output bytes") style "app_small"
            input value VariableInputValue("settings_output_limit") xfill True
            text _("Maximum context message characters") style "app_small"
            input value VariableInputValue("settings_context_limit") xfill True

            hbox:
                spacing 10
                textbutton _("Save settings") action Function(save_settings_action)
                textbutton _("Reset settings") action Confirm(_("Restore default settings?"), Function(controller.reset_settings))

screen workspace_panel():
    hbox:
        spacing 20
        vbox:
            xsize 620
            spacing 8
            text _("System prompt") size 28 bold True
            input value VariableInputValue("system_prompt_text") multiline True xfill True ymaximum 250
            hbox:
                spacing 8
                textbutton _("Save prompt") action Function(save_prompt_action)
                textbutton _("Reset prompt") action Confirm(_("Reset the system prompt?"), Function(controller.reset_system_prompt))

            text _("Memory") size 28 bold True
            input value VariableInputValue("memory_text") multiline True xfill True ymaximum 250
            hbox:
                spacing 8
                textbutton _("Save memory") action Function(save_memory_action)
                textbutton _("Reset memory") action Confirm(_("Reset memory?"), Function(controller.reset_memory))

        vbox:
            xsize 500
            spacing 8
            text _("History") size 28 bold True
            for date in history_dates:
                textbutton date action Function(controller.load_history_date_async, date)
            text "[_('Selected:')] [history_selected_date]" style "app_small"
            viewport:
                ymaximum 430
                mousewheel True
                text history_content style "app_small"
            textbutton _("Clear all history") action Confirm(_("Clear all history?"), Function(controller.reset_history))

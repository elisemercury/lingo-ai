import streamlit as st
from typing import Dict, List
import requests
import prompts

error_msg = "Oops, something went wrong! 😿"

## Initialize App Data
def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""
    if 'source_text' not in st.session_state:
        st.session_state.source_text = ""
    if 'target_text' not in st.session_state:
        st.session_state.target_text = ""
    if 'current_formality' not in st.session_state:
        st.session_state.current_formality = 1  # Scale from 0 (very informal) to 2 (very formal)
    if 'current_mood' not in st.session_state:
        st.session_state.current_mood = 1  # Scale from 0 (very happy) to 2 (very serious)
    if 'selected_gender' not in st.session_state:
        st.session_state.selected_gender = "None"  # Default to none
    if 'translation_complete' not in st.session_state:
        st.session_state.translation_complete = False
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "gemini-1.5-flash-latest"  # Default model

def get_language_list() -> list[str]:
    """Return a sorted list of supported languages"""
    return sorted([
        "Arabic", "Bengali", "Bulgarian", "Chinese simplified", "Chinese traditional",
        "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Finnish",
        "French", "German", "Greek", "Hebrew", "Hindi", "Hungarian", "Indonesian",
        "Italian", "Japanese", "Korean", "Latvian", "Lithuanian", "Norwegian",
        "Polish", "Portuguese", "Romanian", "Russian", "Serbian", "Slovak",
        "Slovenian", "Spanish", "Swahili", "Swedish", "Thai", "Turkish",
        "Ukrainian", "Vietnamese", "Afrikaans", "Amharic", "Assamese", "Azerbaijani",
        "Belarusian", "Bosnian", "Catalan", "Cebuano", "Corsican", "Welsh",
        "Dhivehi", "Esperanto", "Basque", "Persian", "Filipino (Tagalog)", "Frisian",
        "Irish", "Scots Gaelic", "Galician", "Gujarati", "Hausa", "Hawaiian",
        "Hmong", "Haitian Creole", "Armenian", "Igbo", "Icelandic", "Javanese",
        "Georgian", "Kazakh", "Khmer", "Kannada", "Krio", "Kurdish", "Kyrgyz",
        "Latin", "Luxembourgish", "Lao", "Malagasy", "Maori", "Macedonian",
        "Malayalam", "Mongolian", "Meiteilon (Manipuri)", "Marathi", "Malay",
        "Maltese", "Myanmar (Burmese)", "Nepali", "Nyanja (Chichewa)",
        "Odia (Oriya)", "Punjabi", "Pashto", "Sindhi", "Sinhala (Sinhalese)",
        "Samoan", "Shona", "Somali", "Albanian", "Sesotho", "Sundanese", "Tamil",
        "Telugu", "Tajik", "Uyghur", "Urdu", "Uzbek", "Xhosa", "Yiddish",
        "Yoruba", "Zulu"
    ])

def get_gendered_languages() -> List[str]:
    """Return a list of languages that commonly use grammatical gender"""
    return [
        "Arabic", "Czech", "Danish", "Dutch", "French", "German", "Greek", "Hebrew", "Hindi", "Italian", "Kannada", "Latin",
        "Latvian", "Lithuanian", "Polish", "Portuguese", "Romanian", "Russian", "Slovak", "Slovenian", "Spanish",
        "Swedish", "Welsh"
    ]

def create_model_options() -> Dict[str, str]:
    """Create mapping of display names to model identifiers"""
    return {
        "Gemini 1.5 Flash (Faster)": "gemini-1.5-flash-latest",
        "Gemini 1.5 Pro (More capable)": "gemini-1.5-pro-latest"
    }

# App Functions
def swap_languages():
    """Swap source and target languages"""
    if 'source_lang' in st.session_state and 'target_lang' in st.session_state:
        # Store current values
        temp_source = st.session_state.source_lang
        temp_target = st.session_state.target_lang
        temp_source_text = st.session_state.source_text
        temp_target_text = st.session_state.target_text

        # Delete the existing keys to allow modification
        del st.session_state.source_lang
        del st.session_state.target_lang
        
        # Set new values
        st.session_state["source_lang"] = temp_target
        st.session_state["target_lang"] = temp_source
        
        # Swap the text if a translation has been completed
        if st.session_state.translation_complete:
            st.session_state.source_text = temp_target_text
            st.session_state.target_text = ""
            st.session_state.translation_complete = False

def handle_swap():
    """Handler for swap button click"""
    st.session_state.swap_clicked = True

def adjust_settings(adjustment_type: str):
    """Adjust the tone based on button clicks"""
    if adjustment_type == "less_formal":
        st.session_state.current_formality = max(0, st.session_state.current_formality - 1)
    elif adjustment_type == "more_formal":
        st.session_state.current_formality = min(2, st.session_state.current_formality + 1)
    elif adjustment_type == "more_fun":
        st.session_state.current_mood = max(0, st.session_state.current_mood - 1)
    elif adjustment_type == "more_serious":
        st.session_state.current_mood = min(2, st.session_state.current_mood + 1)

def call_ai_studio_api(text: str, api_key: str, source_lang: str, target_lang: str, 
                      formality: int, mood: int, gender: str) -> str:
    """Call the Google AI Studio API for translation"""
    formality_terms = ["very informal", "neutral", "very formal"]
    mood_terms = ["very happy", "neutral", "very serious"]
    
    args = {
        'source_lang': source_lang,
        'target_lang': target_lang,
        'formality': formality_terms[formality],
        'mood': mood_terms[mood],
        'gender': gender,
        'text': text
    }

    # Building the prompt
    prompt = f"""{prompts.role}
                 {prompts.rules}
                 {prompts.instructions.format(**args)}
                 """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{st.session_state.selected_model}:generateContent"
    
    headers = {"Content-Type": "application/json"}
    
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.1
        }
    }
    
    try:
        response = requests.post(
            f"{url}?key={api_key}",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if "candidates" in response_data:
                translated_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
                return translated_text
            else:
                print("Error: No translation candidate found in response")
                return error_msg
        else:
            print(f"Error: API request failed with status code {response.status_code}\n{response.text}")
            return error_msg
            
    except Exception as e:
        print(f"Error making API request: {str(e)}")
        return error_msg

# Main
def main():
    st.set_page_config(
        page_title="Lingo.ai",
        page_icon="🌉",
        layout="wide"
    )
    
    # Custom layout
    st.markdown("""
        <style>
            .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
                padding-left: 5rem;
                padding-right: 5rem;
            }
            .swap-button-container {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100%;
                padding-top: 1.5rem;
            }
            .stButton button {
                width: 100%;
            }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session
    initialize_session_state()

    # Initialize swap_clicked state if it doesn't exist
    if 'swap_clicked' not in st.session_state:
        st.session_state.swap_clicked = False

    # Handle swap if button was clicked
    if st.session_state.swap_clicked:
        swap_languages()
        st.session_state.swap_clicked = False

    # App Body
    st.title("🌉 Lingo.ai")
    tab1, tab2 = st.tabs(["Translate", "Settings"])

    #### Tab: Settings ####
    with tab2:
        st.markdown('<span style="font-size: 14px">Lingo.ai is powered by Google [Gemini](https://deepmind.google/technologies/gemini/). To use it, please provide your [Google AI Studio API Key](https://aistudio.google.com/app/apikey) below.</span>', unsafe_allow_html=True)
        api_key = st.text_input(
            "Google AI Studio API Key",
            type="password",
            value=st.session_state.api_key,
            help="Enter your Google AI Studio API key here"
        )
        st.session_state.api_key = api_key
        
        with st.expander("Advanced Settings"):
            model_options = create_model_options()
            selected_model_name = st.selectbox(
                "Model",
                options=model_options.keys(),
                index=list(model_options.values()).index(st.session_state.selected_model),
                help="Choose between faster response times (Flash) or higher capability (Pro)"
            )
            st.session_state.selected_model = model_options[selected_model_name]

        st.markdown('<br><hr><center>❤️ Open Source<br><span style="font-size: 14px">[View on GitHub](https://github.com/elisemercury/lingo-ai)</span></center>', unsafe_allow_html=True)

    #### Tab: Translate ####
    with tab1:
        languages = get_language_list()
        gendered_languages = get_gendered_languages()
        
        # Language selection layout
        lang_col1, swap_col, lang_col2 = st.columns([10, 1, 10])
        
        with lang_col1:
            source_lang = st.selectbox(
                "Source Language",
                options=languages,
                key="source_lang"
            )

        with swap_col:
            st.markdown(
                '<div class="swap-button-container">',
                unsafe_allow_html=True
            )
            if st.button("🔄", help="Swap languages", key="swap_button", on_click=handle_swap):
                pass  # The actual swap is handled by the on_click callback
            st.markdown('</div>', unsafe_allow_html=True)

        with lang_col2:
            target_lang = st.selectbox(
                "Target Language",
                options=[lang for lang in languages if lang != source_lang],
                key="target_lang"
            )
        
        # Text input/output areas
        text_col1, text_col2 = st.columns(2)
        
        with text_col1:
            source_text = st.text_area(
                "Enter text to translate",
                height=200,
                value=st.session_state.source_text,
                help="Supports Markdown formatting"
            )
            st.session_state.source_text = source_text

        with text_col2:
            target_text = st.text_area(
                "Translation",
                value=st.session_state.target_text,
                height=200,
                disabled=not st.session_state.translation_complete,
                help="Translation will appear here. You can edit after translation is complete."
            )
            
            if st.session_state.translation_complete:
                st.session_state.target_text = target_text
        if not api_key:
                st.error("⚠️ Please enter your Google AI Studio API key in the Settings tab to start translating.")

        # Centered translate button
        col1, col2, col3 = st.columns([4, 4, 4])

        with col2:
            # Translate Button
            if st.button("Translate", type="primary", disabled=not api_key, use_container_width=True):
                if source_text:
                    with st.spinner("Translating..."):
                        gender = st.session_state.selected_gender if target_lang in gendered_languages else "None"
                        
                        translation = call_ai_studio_api(
                            text=source_text,
                            api_key=st.session_state.api_key,
                            source_lang=source_lang,
                            target_lang=target_lang,
                            formality=st.session_state.current_formality,
                            mood=st.session_state.current_mood,
                            gender=gender
                        )
                        
                        st.session_state.target_text = translation
                        st.session_state.translation_complete = True
                        st.rerun()
                else:
                    st.warning("Please enter text to translate")
        
        # Translation settings
        with st.expander("Translation Settings"):
            tone_col1, tone_col2, tone_col3 = st.columns(3)
            
            with tone_col1:
                st.markdown("##### Formality")
                formality_cols = st.columns(2)
                with formality_cols[0]:
                    if st.button("📉 Less Formal", use_container_width=True):
                        adjust_settings("less_formal")
                        st.rerun()
                with formality_cols[1]:
                    if st.button("📈 More Formal", use_container_width=True):
                        adjust_settings("more_formal")
                        st.rerun()
                
                formality_labels = ["Very Informal", "Neutral", "Very Formal"]
                st.progress(st.session_state.current_formality / 2)
                st.caption(f"Current: {formality_labels[st.session_state.current_formality]}")

            with tone_col2:
                st.markdown("##### Mood")
                mood_cols = st.columns(2)
                with mood_cols[0]:
                    if st.button("😊 More Fun", use_container_width=True):
                        adjust_settings("more_fun")
                        st.rerun()
                with mood_cols[1]:
                    if st.button("🎯 More Serious", use_container_width=True):
                        adjust_settings("more_serious")
                        st.rerun()
                
                mood_labels = ["Very Happy", "Neutral", "Very Serious"]
                st.progress(st.session_state.current_mood / 2)
                st.caption(f"Current: {mood_labels[st.session_state.current_mood]}")

            with tone_col3:
                st.markdown("##### Gendering")
                if target_lang in gendered_languages:
                    gender_options = ["None", "Female", "Male"]
                    selected_gender = st.selectbox(
                        "Select gender for translation",
                        options=gender_options,
                        index=gender_options.index(st.session_state.selected_gender),
                        help="Select the gender for grammatical agreement in the target language",
                        label_visibility="collapsed"
                    )
                    st.session_state.selected_gender = selected_gender
                    st.caption("If a gender is selected, the translated output will be gendered accordingly.")
                else:
                    st.caption("Gender selection not applicable for this language")
                    st.session_state.selected_gender = "None"

if __name__ == "__main__":
    main()
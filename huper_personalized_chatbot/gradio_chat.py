import gradio as gr
import requests

API_URL = "http://localhost:8000"  # Adjust if your backend is on a different host/port


def chat(message, history, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(f"{API_URL}/chat", json={"content": message}, headers=headers)
    if response.status_code == 200:
        bot_message = response.json()['content']
        history.append((message, bot_message))
        return "", history
    else:
        error_message = f"Error: {response.json()['detail']}"
        history.append((message, error_message))
        return "", history


with gr.Blocks() as demo:
    gr.Markdown("# Personalized Chat Interface")

    access_token_input = gr.Textbox(label="Access Token")
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    clear = gr.Button("Clear")

    msg.submit(chat, [msg, chatbot, access_token_input], [msg, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch()
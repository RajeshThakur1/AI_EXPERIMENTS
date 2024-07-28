import gradio as gr
import requests

# Backend API URL
API_URL = "http://localhost:8000"  # Adjust this if your backend is on a different host/port


def register_user(username, email, password):
    response = requests.post(f"{API_URL}/register", json={"username": username, "email": email, "password": password})
    if response.status_code == 200:
        return f"Registration successful. Access token: {response.json()['access_token']}"
    else:
        return f"Error: {response.json()['detail']}"


def login_user(username, password):
    response = requests.post(f"{API_URL}/token", data={"username": username, "password": password})
    if response.status_code == 200:
        return f"Login successful. Access token: {response.json()['access_token']}"
    else:
        return f"Error: {response.json()['detail']}"


def create_user_profile(access_token, preferences, interests):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(f"{API_URL}/profile", json={"preferences": preferences, "interests": interests},
                             headers=headers)
    if response.status_code == 200:
        return response.json()['message']
    else:
        return f"Error: {response.json()['detail']}"


def update_user_profile(access_token, preferences, interests):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.put(f"{API_URL}/profile", json={"preferences": preferences, "interests": interests},
                            headers=headers)
    if response.status_code == 200:
        return response.json()['message']
    else:
        return f"Error: {response.json()['detail']}"


def get_user_profile(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{API_URL}/profile", headers=headers)
    if response.status_code == 200:
        data = response.json()
        return f"Preferences: {data['preferences']}, Interests: {data['interests']}"
    else:
        return f"Error: {response.json()['detail']}"


# Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# Hyper personalization chatbot System")

    with gr.Tab("Register"):
        username_input = gr.Textbox(label="Username")
        email_input = gr.Textbox(label="Email")
        password_input = gr.Textbox(label="Password", type="password")
        register_button = gr.Button("Register")
        register_output = gr.Textbox(label="Result")
        register_button.click(register_user, inputs=[username_input, email_input, password_input],
                              outputs=register_output)

    with gr.Tab("Login"):
        login_username = gr.Textbox(label="Username")
        login_password = gr.Textbox(label="Password", type="password")
        login_button = gr.Button("Login")
        login_output = gr.Textbox(label="Result")
        login_button.click(login_user, inputs=[login_username, login_password], outputs=login_output)

    with gr.Tab("Profile"):
        access_token_input = gr.Textbox(label="Access Token")
        preferences_input = gr.Textbox(label="Preferences")
        interests_input = gr.Textbox(label="Interests")
        create_profile_button = gr.Button("Create Profile")
        update_profile_button = gr.Button("Update Profile")
        get_profile_button = gr.Button("Get Profile")
        profile_output = gr.Textbox(label="Result")
        create_profile_button.click(create_user_profile,
                                    inputs=[access_token_input, preferences_input, interests_input],
                                    outputs=profile_output)
        update_profile_button.click(update_user_profile,
                                    inputs=[access_token_input, preferences_input, interests_input],
                                    outputs=profile_output)
        get_profile_button.click(get_user_profile, inputs=[access_token_input], outputs=profile_output)

if __name__ == "__main__":
    demo.launch()
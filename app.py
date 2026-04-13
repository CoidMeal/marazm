import streamlit as st

# Title of the app
st.title('Stress Management Application')

# Description
st.write('This application provides tools to manage stress levels effectively.')

# User input for stress level
stress_level = st.slider('How stressed do you feel today?', min_value=0, max_value=10, value=5)

# Display stress level
st.write('Your stress level is:', stress_level)

# Suggestions based on stress level
if stress_level < 4:
    st.write("You're doing great! Keep it up!")
elif stress_level < 7:
    st.write("Consider taking some time for relaxation.")
else:
    st.write("It's important to reach out and talk to someone. Consider a break!")

# Footer
st.write('Remember to take care of your mental health!')
import streamlit as st
import joblib
import numpy as np

try:
    model = joblib.load('asd_model.pkl')
    st.success("Model loaded successfully!") 
except Exception as e:
    st.error(f"Model file not found! : {e}")
    st.stop()

st.set_page_config(page_title="ASD Screening ", layout="centered")

st.title(" Child ASD Screening Assistant")
st.write("Please answer these 10 questions based on the child's behavior.")

questions = [
    "Does the child often notice small sounds when others do not?",
    "Does the child concentrate more on the whole picture than small details?",
    "In a social group, can they easily keep track of conversations?",
    "Does the child find it easy to switch between activities?",
    "Does the child find it hard to keep a conversation going?",
    "Is the child good at social 'chit-chat'?",
    "Do they find it hard to work out characters' intentions in stories?",
    "Did they enjoy pretend-play games as a preschooler?",
    "Is it easy for them to read feelings from faces?",
    "Does the child find it hard to make new friends?"
]

user_answers = []
for i, q in enumerate(questions):
    ans = st.radio(f"Q{i+1}: {q}", ("No", "Yes"), horizontal=True, key=f"q{i}")
    user_answers.append(1 if ans == "Yes" else 0)

# The Logic to Run the Assessment
if st.button("Run Assessment"):
    # Reshape input for the model
    features = np.array(user_answers).reshape(1, -1)
    
    # Get the probability
    prob = model.predict_proba(features)[0][1]
    
    st.divider()
    
    # Apply your "Levels"
    if prob < 0.30:
        st.success(f"**LOW LIKELIHOOD** ({prob*100:.1f}%)")
        st.write("The screening suggests typical developmental traits.")
    elif 0.30 <= prob < 0.77:
        st.warning(f"**MEDIUM LIKELIHOOD** ({prob*100:.1f}%)")
        st.write("Some traits were detected. Monitoring or a follow-up is advised.")
    else:
        st.error(f"**HIGH LIKELIHOOD** ({prob*100:.1f}%)")
        st.write("A high concentration of traits was identified. Clinical referral is recommended.")
import { initializeApp } from "firebase/app";
import { getDatabase } from "firebase/database";

const firebaseConfig = {
  apiKey: "AIzaSyA_dNp20zhoEV9bsgq_CO7M8MCQ_NtLlG8",
  authDomain: "jandhwanni.firebaseapp.com",
  projectId: "jandhwanni",
  storageBucket: "jandhwanni.firebasestorage.app",
  messagingSenderId: "579157886498",
  appId: "1:579157886498:web:5965fa9074123ad4dc2c7b",
  measurementId: "G-64635RC3G2",
  databaseURL: "https://jandhwanni-default-rtdb.firebaseio.com/"
};

const app = initializeApp(firebaseConfig);
export const database = getDatabase(app);

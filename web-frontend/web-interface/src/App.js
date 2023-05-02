import React, {useEffect, useState} from 'react';
import io from 'socket.io-client';
import {v4 as uuidv4} from 'uuid';

import './App.css';
import Chatbox from './components/Chatbox';
import Document from './components/Document';
import EndSession from './components/EndSession';
import EndScreen from './components/EndScreen';
import Login from './components/Login';
import Help from './components/Help'

function App() {
    const [doc, setDoc] = useState([]);
    const [sketch, setSketch] = useState([]);
    const [wholeDoc, setWholeDoc] = useState({});
    const [code, setCode] = useState("");
    const [sessionActive, setSessionActive] = useState(true);
    const [uuid, setUuid] = useState(uuidv4());

    const queryParams = new URLSearchParams(window.location.search);
    const mode = queryParams.get('mode');
    const pid = queryParams.get('pid');

    const [socket, setSocket] = useState(null);

    const addr = window.location.origin.split(":3000")[0];

    useEffect(() => {
        if (code.length > 0 && sessionActive) {
            fetch(addr + ':8000/startup', {
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json"
                },
                method: "POST",
                body: JSON.stringify({code: code, id: uuid, mode: mode}),
            });
        }
    }, [code])

    useEffect(() => {
        const newSocket = io(addr + ':8000');
        setSocket(newSocket);
        return () => newSocket.close();
    }, [setSocket]);

    useEffect(() => {
        const docListener = (doc) => {
            if (doc['id'] === uuid) {
                setDoc(doc['document']);
                setSketch(doc['sketch']);
                setWholeDoc(JSON.parse(JSON.stringify(doc)));
                //setWholeDoc(doc["highlight_coeff"])
            }
        };

        if (socket) {
            socket.on('document', docListener);
            return () => {
                socket.off('document', docListener);
            };
        }
    }, [socket, code]);

    useEffect(() => {
        const killListener = (kill) => {
            if (kill['id'] === uuid) {
                //setCode("");
                setSessionActive(false);
                setDoc([]);
                setSketch([]);
                setWholeDoc({})
                socket.close();
                setSocket(null);
            }
        };
        if (socket) {
            socket.on('kill_session', killListener);
            return () => {
                socket.off('kill_session', killListener);
            };
        }
    }, [socket]);

    useEffect(() => {
        document.title = "Experiments (Georgia Tech)"
    })

    return (
        <div className="App">
            <h1>Creative Wand Experiment System</h1>
            <Help/>
            {/*<h3>Your goal: Make a story with <i>creative wand</i> that start from (Subgoal 1)<u>talking about*/}
            {/*    business </u>*/}
            {/*    and ends in (subgoal 2)<u>something related to sports</u>,*/}
            {/*    (subgoal 3)<u>mentioning soccer.</u></h3>*/}

            {code.length > 0 && sessionActive ?
                <div>
                    <EndSession setSessionActive={setSessionActive} code={code} setCode={setCode} uuid={uuid}/>
                    <Chatbox socket={socket} code={code} mode={mode} uuid={uuid}/>
                    <Document doc={doc} setDoc={setDoc} sketch={sketch} setSketch={setSketch} wholeDoc={wholeDoc}
                              setWholeDoc={setWholeDoc}/>
                </div>
                : (
                    sessionActive ?
                        <Login code={code} setCode={setCode} mode={mode} pid={pid}/>
                        :
                        <EndScreen mode={mode} code={code} pid={pid}/>
                )
            }

        </div>
    );
}

export default App;

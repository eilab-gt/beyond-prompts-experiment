import React, {useEffect, useState} from 'react';
import Login from "./Login";
import {Link, Router} from "react-router-dom";
import {v4 as uuidv4} from 'uuid';


const Landing = (props) => {
    const [uuid, setUuid] = useState(uuidv4());
    const [backupMode, setBackupMode] = useState();
    const [backupPID, setBackupPID] = useState();
    const [backupLink, setBackupLink] = useState();

    const linkTarget = {
        pathname: "/?mode=2",
        key: uuidv4(), // we could use Math.random, but that's not guaranteed unique.
        state: {
            applied: true
        }
    };


    function linkWithMode(mode) {
        let myObject = {
            pathname: "/?mode=" + mode,
            key: uuidv4(), // we could use Math.random, but that's not guaranteed unique.
            state: {
                applied: true
            }
        }
        return myObject;


    }


    function getBackupLink() {
        if (backupMode === undefined || backupPID === undefined) {
            return "You will see a link here once you entered mode and PID."
        }
        return "/?mode=" + backupMode + "&pid=" + backupPID
    }

    useEffect(() => {
        setBackupLink(getBackupLink())
    }, [backupMode, backupPID])

    return (
        <div style={{marginBottom: 32}}>
            {/*<h2>===PILOT / DEBUG ===</h2>*/}
            {/*<h1 style={{color: "red"}}>Manual mode selection FOR PILOT only, remove manual mode selection when*/}
            {/*    deployed!</h1>*/}
            <h2>Click "Help" at any time if you need to check instructions.</h2>
            {/*<br/>*/}
            <h2>In case you accidentally closed the survey window, just reopen it - Your progress is automatically
                saved.</h2>
            If things doesn't work, please send a message to us reporting what is happening.
            <br/>
            Debug info: Mode {props.mode}
            <br/>
            {/*{props.mode === null ?*/}
            {/*    <div>*/}
            {/*        <h2>You don't have a mode in your url parameter!</h2>*/}
            {/*        Valid modes are:*/}
            {/*        <ul>*/}
            {/*            <li>test</li>*/}
            {/*            <li>test_global</li>*/}
            {/*            <li>test_local</li>*/}
            {/*            <li>test_elaboration</li>*/}
            {/*            <li>test_reflection</li>*/}
            {/*            <li>test_human</li>*/}
            {/*            <li>test_agent</li>*/}
            {/*        </ul>*/}


            {/*        <br/>*/}
            {/*        <input type="text" placeholder="Mode"*/}
            {/*               onChange={event => setBackupMode(event.target.value)}*/}
            {/*               required/>*/}
            {/*        <input type="text" placeholder="Participant ID (Logging identifier)"*/}
            {/*               onChange={event => setBackupPID(event.target.value)}*/}
            {/*               required/>*/}
            {/*        <br/>*/}
            {/*        <a href={backupLink}>{backupLink}</a>*/}
            {/*    </div>*/}
            {/*    :*/}
            {/*    <div>*/}
            {/*        Mode {props.mode}*/}
            {/*    </div>*/}
            {/*}*/}
        </div>
    );
}

export default Landing;
import React, {useEffect, useState} from 'react';
import Landing from './Landing';
import Help from "./Help";

class Login extends React.Component {


    constructor(props) {
        super(props);
        this.setCode = props.setCode
        this.pid = props.pid
        this.state = {
            tempCode: this.pid,
        }
    }

    componentDidMount() {
        this.setState({tempCode: this.pid})
    }


    render() {
        //const [tempCode, setTempCode] = useState("");


        const submitCode = async (event) => {
            event.preventDefault();
            //this.props.setCode(tempCode);
            this.setCode(this.state.tempCode)

            // fetch('http://localhost:8000/session_code', {
            //     headers: {
            //       Accept: "application/json",
            //       "Content-Type": "application/json",
            //     },
            //     method: "POST",
            //     body: JSON.stringify({code: tempCode}),
            // });

        }


        return (
            <div>
                <Landing mode={this.props.mode}/>
                {this.props.mode === null?
                    <div>Missing experiment parameters - please re-click the link in the survey, thank you.</div>
                :<form onSubmit={submitCode}>
                    {/*<input type="text" placeholder="Sign In Code" hidden={true}*/}
                    {/*       onChange={event => this.setState({tempCode: event.target.value})}*/}
                    {/*       defaultValue={this.state.tempCode} value={this.tempCode} required/>*/}
                    <input style={{fontSize: 32}} type="submit" value="Start!"/>
                </form>
                }

            </div>
        );
    }
}

//value={tempCode}

export default Login;
  
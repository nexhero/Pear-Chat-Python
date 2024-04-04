import {spawn} from 'bare-subprocess'
import Hyperswarm from 'hyperswarm'
import crypto from 'hypercore-crypto'
import b4a from 'b4a'
const { teardown } = Pear

const swarm = new Hyperswarm()

const command = './main.py';
const args = []
const subprocess = spawn(command, args);

swarm.on('connection',(peer)=>{
  const name = b4a.toString(peer.remotePublicKey,'hex').substr(0,6)
  peer.on('data',message => streamMessage(name,message))
  peer.on('error',e=>console.log('Connection error: ${e}'))

})

swarm.on('update',()=>{
  console.log('# peers:',swarm.connections.size)
})

function streamMessage(name,message){
  const data ={
    task:'message',
    from:name,
    message:message.toString()
  }
  subprocess.stdin.write(JSON.stringify(data))
}

async function joinSwarm(topicStr){
  const topicBuffer = b4a.from(topicStr, 'hex')
  const discovery = swarm.join(topicBuffer, { client: true, server: true })
  await discovery.flushed()
  const topic = b4a.toString(topicBuffer, 'hex')
  const data ={
    task:'join_channel',
    status:'ok'
  }
  subprocess.stdin.write(JSON.stringify(data))
}


////////////////////////
// Listen for actions //
////////////////////////
subprocess.stdout.on('data', (data) => {
  try {
    const action = JSON.parse(data)
    if (action.action === 'join_channel') {
      joinSwarm(action.data)
    }
    if (action.action === 'send') {
      console.log("sending message",action.data)
      const peers = [...swarm.connections]
      for (const peer of peers) peer.write(action.data)
    }
    if (action.action === 'create_channel') {
      console.log("creating channel...")
      const topicBuffer = crypto.randomBytes(32)
      const topic = b4a.toString(topicBuffer, 'hex')
      joinSwarm(topic)
      const data ={
        task:'create_channel',
        channel:topic,
        status:'ok'
      }
      subprocess.stdin.write(JSON.stringify(data))
      console.log('Channel:',data)

    }
  } catch (err) {
    console.log("unable to parse")
  }

});
